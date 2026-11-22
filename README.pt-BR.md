<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/Read%20in-English-2f6fed?style=for-the-badge" alt="Read in English"></a>
</p>

<p align="center">
  <img src="icon/icon.png" width="128" alt="Ícone do Meerkat">
</p>

<h1 align="center">Meerkat</h1>

<p align="center">
  Seus pull requests do GitHub na barra de menu (macOS) e na bandeja do sistema (Windows).<br>
  Revisões esperando por você · status do CI · stacked PRs que precisam de rebase
</p>

---

Como um suricato de sentinela, o Meerkat fica de olho nos seus PRs e avisa quando algo precisa de você:
pediram sua revisão, o CI falhou, revisaram seu PR ou o pai de uma pilha de PRs foi mergeado e o filho
precisa de rebase. Sem precisar abrir o navegador.

## Recursos

- **Contador na barra de menu** com tudo o que precisa de uma ação sua.
- **Menu a um clique**, em *Precisam da sua revisão* e *Meus PRs*; clique num PR para abri-lo.
- **Status de relance:** ❌ CI falhou · 🟡 CI rodando · 💬 mudanças pedidas · ✅ aprovado ·
  ⏳ aguardando revisão · 📝 rascunho · 🔁 rebase necessário.
- **Stacked PRs:** os filhos aparecem aninhados sob o pai (um PR cuja base é a branch de outro). Quando o pai é
  mergeado, os filhos ficam 🔁 até você dar push do rebase.
- **Notificações nativas** para revisões pedidas, CI falhando, revisões e comentários nos seus PRs e pais
  mergeados. A primeira atualização após abrir o app nunca notifica.
- **Escolha quais repositórios vigiar** (Settings → Watched repositories).
- Intervalo de atualização (1/2/5/10 min), pausar notificações por 1h, iniciar com o sistema, inglês ou
  português.
- Nunca altera seu código nem seus repositórios: só lê a API do GitHub.

## Instalação

Baixe em [Releases](https://github.com/railima/meerkat/releases): `Meerkat.dmg` (macOS 13+) ou
`Meerkat.exe` (Windows). Os apps não são assinados: no macOS, na primeira vez clique com o botão direito →
**Abrir**; no Windows, SmartScreen → **Mais informações → Executar assim mesmo**.

Para compilar: `./build_mac.sh` (macOS, requer o [uv](https://docs.astral.sh/uv/)) ou `build_windows.bat`
(Windows, requer Python 3.12+).

## Login

Se o [GitHub CLI](https://cli.github.com) estiver logado (`gh auth login`), o Meerkat usa ele
automaticamente. Senão, use **Settings → GitHub token…** e cole um token pessoal com escopo `repo` (leitura
basta).

## Privacidade

- O token fica no Chaveiro do macOS / Gerenciador de Credenciais do Windows, nunca em arquivo.
- O único tráfego de rede é para `api.github.com` (uma consulta GraphQL por atualização).
- Configurações e memória das pilhas ficam em `~/Library/Application Support/Meerkat` ou
  `%APPDATA%\Meerkat`.

## Como funciona

```
github_api.py   consulta GraphQL e conversão em objetos PR
stacks.py       árvore de pilhas e detecção de "rebase necessário" (lembra os pais entre atualizações)
events.py       compara atualizações para decidir o que notificar
menu.py         conteúdo do menu (puro, testado)
tray.py         ícone e menu na bandeja (pystray)
notifier.py     notificações nativas
autostart.py    LaunchAgent (macOS) / chave Run do registro (Windows)
config.py       configurações, memória das pilhas e token (keyring)
i18n.py         textos em inglês e português
app.py          laço de atualização
```

Testes: `.venv/bin/pytest`. Publicar uma versão: `git tag v0.1.0 && git push --tags` (o CI gera o `.dmg` e
o `.exe` e anexa à Release).

## Licença

[MIT](LICENSE)
