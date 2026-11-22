"""Ícone na barra de menu/bandeja e o menu (pystray)."""

import sys
import time
import webbrowser
from datetime import datetime, timezone
from functools import partial

import pystray
from pystray import Menu, MenuItem

import autostart
import config
from i18n import LANGUAGES, ago, t
from icons import tray_icon
from menu import entries
from model import attention_count

INTERVALS = (1, 2, 5, 10)


def on_main_thread(fn):
    """No macOS, mexer no menu/ícone fora da thread principal pode travar o app."""
    if sys.platform == "darwin":
        from PyObjCTools import AppHelper

        AppHelper.callAfter(fn)
    else:
        fn()


def _open_url(url, _icon=None, _item=None):
    webbrowser.open(url)


class Tray:
    def __init__(self, app):
        self.app = app
        self.icon = pystray.Icon("meerkat", tray_icon(0, False), "Meerkat", menu=Menu(self._items))

    # ---------- Menu ----------
    # Ações com parâmetro usam functools.partial: o pystray recusa lambdas com mais de 2 argumentos
    # (parâmetros com valor padrão também contam).

    def _items(self):
        lang, app = config.setting("ui_language"), self.app
        if app.error:
            kind, detail = app.error
            text = t("error_auth", lang) if kind == "auth" else t("error_network", lang, detail=detail)
            yield MenuItem(text, None, enabled=False)
            yield Menu.SEPARATOR
        if app.state:
            for entry in entries(app.state, datetime.now(timezone.utc), lang):
                if entry.header:
                    yield MenuItem(entry.text, None, enabled=False)
                else:
                    yield MenuItem(entry.text, partial(_open_url, entry.url))
        else:
            yield MenuItem(t("loading", lang), None, enabled=False)
        yield Menu.SEPARATOR

        if app.updated_at:
            age = time.time() - app.updated_at
            label = t("updated_now", lang) if age < 60 else t("updated", lang, ago=ago(age, lang))
            yield MenuItem(label, None, enabled=False)
        yield MenuItem(t("refresh", lang), lambda: app.refresh_now())
        if app.paused():
            yield MenuItem(t("resume", lang), lambda: self._pause(False))
        else:
            yield MenuItem(t("pause", lang), lambda: self._pause(True))
        yield MenuItem(t("settings", lang), Menu(*self._settings(lang)))
        yield MenuItem(t("quit", lang), lambda: app.quit())

    def _settings(self, lang):
        interval = Menu(*(
            MenuItem(t("minutes", lang, n=n), partial(self._set, interval=n),
                     checked=partial(lambda n, _m: config.setting("interval") == n, n), radio=True)
            for n in INTERVALS
        ))
        language = Menu(*(
            MenuItem(name, partial(self._set, ui_language=code),
                     checked=partial(lambda code, _m: config.setting("ui_language") == code, code), radio=True)
            for code, name in LANGUAGES.items()
        ))
        muted = set(config.setting("muted_repos"))
        repo_items = [
            MenuItem(repo, partial(lambda repo, _i, _m: self.app.toggle_repo(repo), repo),
                     checked=partial(lambda repo, _m: repo not in set(config.setting("muted_repos")), repo))
            for repo in sorted(set(self.app.repos) | muted)
        ] or [MenuItem(t("repos_empty", lang), None, enabled=False)]
        repos = Menu(*repo_items)
        return (
            MenuItem(t("repos", lang), repos),
            MenuItem(t("interval", lang), interval),
            MenuItem(t("language", lang), language),
            MenuItem(t("token", lang), lambda: self.app.ask_token()),
            MenuItem(t("start_at_login", lang), lambda: self._toggle_autostart(),
                     checked=lambda _m: autostart.is_enabled()),
        )

    def _set(self, _icon=None, _item=None, **values):
        config.save_config(**values)
        self.app.refresh_now()

    def _pause(self, paused):
        config.save_config(paused_until=time.time() + 3600 if paused else 0)
        self.update()

    def _toggle_autostart(self):
        autostart.set_enabled(not autostart.is_enabled())
        self.update()

    # ---------- Ícone ----------

    def update(self):
        app = self.app
        count = attention_count(app.state) if app.state else 0
        error = app.error is not None

        def apply():
            # macOS: número em texto ao lado do ícone; Windows: desenhado no ícone.
            self.icon.icon = tray_icon(0 if sys.platform == "darwin" else count, error)
            self.icon.title = f"Meerkat — {count}" if count else "Meerkat"
            self.icon.update_menu()
            item = getattr(self.icon, "_status_item", None)
            if sys.platform == "darwin" and item is not None:
                item.button().setTitle_(f" {count}" if count else "")

        on_main_thread(apply)

    def run(self, on_ready):
        def setup(icon):
            icon.visible = True
            on_ready()

        self.icon.run(setup=setup)

    def stop(self):
        self.icon.stop()
