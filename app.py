"""Meerkat: painel de PRs do GitHub na barra de menu/bandeja."""

import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timezone

import config
import notifier
from events import diff
from github_api import AuthError, GitHubError, OfflineError, fetch, gh_cli_token, parse
from i18n import notification, t
from model import State, without_repos
from stacks import analyze
from tray import Tray, on_main_thread


def ask_secret(prompt):
    """Pede um texto oculto ao usuário. Retorna o texto, ou None se cancelou."""
    if sys.platform == "darwin":
        script = ('on run argv\ndisplay dialog (item 1 of argv) default answer "" with hidden answer '
                  'with title "Meerkat"\nreturn text returned of result\nend run')
        result = subprocess.run(["osascript", "-e", script, prompt], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None

    # Windows: tkinter vem com o Python e não depende de PowerShell.
    import tkinter as tk
    from tkinter import simpledialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # sem isso a caixa pode abrir atrás de outras janelas
    try:
        return simpledialog.askstring("Meerkat", prompt, show="*", parent=root)
    finally:
        root.destroy()


class Meerkat:
    def __init__(self):
        self.state = None
        self.error = None  # ("auth", None), ("offline", None) ou ("network", detalhe)
        self.updated_at = None
        self.repos = []  # todos os repositórios vistos na última busca (vigiados ou não)
        self.rebaseline = False  # após mudar os vigiados, a próxima busca não notifica
        self.memory = config.load_memory()
        self.wake = threading.Event()
        self.running = True
        self.tray = Tray(self)

    def paused(self):
        return config.setting("paused_until") > time.time()

    def refresh_now(self):
        self.wake.set()

    def refresh_once(self):
        token = config.load_token() or gh_cli_token()
        if not token:
            raise AuthError("no token")
        raw = parse(fetch(token, datetime.now(timezone.utc)))
        self.repos = sorted({pr.repo for pr in raw.review + raw.mine})
        snapshot = without_repos(raw, set(config.setting("muted_repos")))
        parent, rebase, self.memory = analyze(snapshot.mine, snapshot.merged, self.memory)
        config.save_memory(self.memory)
        state = State(snapshot, parent, rebase)
        # Ao voltar a vigiar um repositório, os PRs dele pareceriam novos: não notifica nessa busca.
        events = [] if self.rebaseline else diff(self.state, state)
        self.rebaseline = False
        self.state, self.error, self.updated_at = state, None, time.time()
        if not self.paused():
            lang = config.setting("ui_language")
            sounds = config.setting("sounds")
            for event in events:
                title, body = notification(event, lang)
                # Vários eventos na mesma busca: só o primeiro toca som, para não virar uma cacofonia.
                notifier.notify(title, body, event.pr.url, sound=event.kind if sounds and event is events[0] else None)

    def loop(self):
        failures = 0
        while self.running:
            try:
                self.refresh_once()
                failures = 0
            except AuthError:
                self.error, failures = ("auth", None), failures + 1
            except OfflineError:
                self.error, failures = ("offline", None), failures + 1
            except GitHubError as e:
                self.error, failures = ("network", str(e)), failures + 1
            except Exception as e:  # nunca deixar a thread morrer: o menu ficaria congelado sem aviso
                traceback.print_exc()
                self.error, failures = ("network", type(e).__name__), failures + 1
            self.tray.update()
            if not failures:
                delay = config.setting("interval") * 60
            elif self.error[0] == "offline":
                delay = 60  # volta logo quando a internet voltar
            else:
                delay = min(600, 30 * 2 ** (failures - 1))
            deadline = time.time() + delay
            # Acorda a cada minuto para atualizar "Atualizado há X" no menu.
            while self.running and time.time() < deadline:
                if self.wake.wait(min(60, deadline - time.time())):
                    break
                self.tray.update()
            self.wake.clear()

    def toggle_repo(self, repo):
        muted = set(config.setting("muted_repos"))
        muted ^= {repo}
        config.save_config(muted_repos=sorted(muted))
        self.rebaseline = True
        self.refresh_now()

    def ask_token(self):
        """Caixa de diálogo nativa para colar o token; vazio volta a usar o login do gh.

        Roda numa thread própria (ver tray.py) para não travar o menu enquanto a caixa está aberta.
        """
        token = ask_secret(t("token_prompt", config.setting("ui_language")))
        if token is None:  # cancelar não altera nada
            return
        if config.save_token(token.strip()):
            self.refresh_now()
        else:
            self.error = ("auth", None)
            self.tray.update()

    def quit(self):
        self.running = False
        self.wake.set()
        self.tray.stop()

    def run(self):
        def ready():
            on_main_thread(notifier.setup)
            threading.Thread(target=self.loop, daemon=True).start()

        self.tray.run(ready)


if __name__ == "__main__":
    Meerkat().run()
