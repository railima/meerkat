<p align="center">
  <a href="README.pt-BR.md"><img src="https://img.shields.io/badge/Leia%20em-Portugu%C3%AAs-2e9e5b?style=for-the-badge" alt="Leia em Português"></a>
</p>

<p align="center">
  <img src="icon/icon.png" width="128" alt="Meerkat icon">
</p>

<h1 align="center">Meerkat</h1>

<p align="center">
  Your GitHub pull requests in the menu bar (macOS) and system tray (Windows).<br>
  Reviews waiting for you · CI status · stacked PRs that need a rebase
</p>

---

Like a meerkat on sentry duty, Meerkat keeps watch over your PRs and calls out when something needs you:
someone requested your review, CI failed, your PR got reviewed, or the parent of a stacked PR was merged
and the child needs a rebase. No browser tab required.

## Features

- **Counter in the menu bar** with everything that needs your action.
- **One-click menu** grouped into *Needs your review* and *My PRs*; click a PR to open it.
- **Status at a glance:** ❌ CI failed · 🟡 CI running · 💬 changes requested · ✅ approved ·
  ⏳ awaiting review · 📝 draft · 🔁 rebase needed.
- **Stacked PRs:** children are nested under their parent (a PR whose base is another PR's branch). When the
  parent is merged, the children are flagged 🔁 until you push the rebase.
- **Native notifications** for review requests, CI failures, reviews/comments on your PRs and merged parents.
  The first refresh after launch never notifies.
- **Choose which repositories to watch** (Settings → Watched repositories).
- Refresh interval (1/2/5/10 min), pause notifications for 1h, start at login, English or Portuguese.
- Never changes your code or repositories: it only reads from the GitHub API.

## Installation

Download from [Releases](https://github.com/railima/meerkat/releases): `Meerkat.dmg` (macOS 13+) or
`Meerkat.exe` (Windows). The apps aren't signed: on macOS right-click → **Open** the first time; on Windows,
SmartScreen → **More info → Run anyway**.

Build it yourself: `./build_mac.sh` (macOS, needs [uv](https://docs.astral.sh/uv/)) or `build_windows.bat`
(Windows, needs Python 3.12+).

## Sign-in

If the [GitHub CLI](https://cli.github.com) is logged in (`gh auth login`), Meerkat uses it automatically.
Otherwise, use **Settings → GitHub token…** to paste a personal access token with `repo` scope (read access
is enough).

## Privacy

- The token is stored in the macOS Keychain / Windows Credential Manager, never in a file.
- The only network traffic is to `api.github.com` (one GraphQL query per refresh).
- Settings and stack memory live in `~/Library/Application Support/Meerkat` or `%APPDATA%\Meerkat`.

## How it works

```
github_api.py   GraphQL query and parsing into PR objects
stacks.py       stack tree and "rebase needed" detection (remembers parents across refreshes)
events.py       compares refreshes to decide what to notify
menu.py         menu content (pure, tested)
tray.py         tray icon and menu (pystray)
notifier.py     native notifications
autostart.py    LaunchAgent (macOS) / Run registry key (Windows)
config.py       settings, stack memory and token (keyring)
i18n.py         English and Portuguese strings
app.py          refresh loop
```

Tests: `.venv/bin/pytest`. Publish a release: `git tag v0.1.0 && git push --tags` (CI builds the `.dmg`
and `.exe` and attaches them).

## License

[MIT](LICENSE)
