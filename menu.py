"""Monta o conteúdo do menu (texto puro; o tray.py transforma em itens do sistema)."""

from dataclasses import dataclass
from datetime import datetime

from i18n import ago, short_ref, t
from model import ORDER, status
from stacks import ordered

EMOJI = {"rebase": "🔁", "failing": "❌", "changes": "💬", "running": "🟡", "draft": "📝",
         "approved": "✅", "waiting": "⏳"}
MAX_PER_SECTION = 15
MAX_TITLE = 55


@dataclass(frozen=True)
class Entry:
    text: str
    url: str | None = None
    header: bool = False  # texto informativo, não clicável


def _title(text):
    return text if len(text) <= MAX_TITLE else text[:MAX_TITLE] + "…"


def _status_text(pr, state, lang):
    s = status(pr, state)
    if s == "rebase":
        parent = state.rebase[pr.id]
        return t("status_conflict", lang) if parent is None else t("status_rebase", lang, parent=parent)
    return t(f"status_{s}", lang)


def _limit(rows, lang):
    if len(rows) <= MAX_PER_SECTION:
        return rows
    return rows[:MAX_PER_SECTION] + [Entry(t("more", lang, n=len(rows) - MAX_PER_SECTION), header=True)]


def entries(state, now, lang):
    snap = state.snapshot
    out = [Entry(t("review_header", lang, n=len(snap.review)), header=True)]
    reviews = []
    for pr in sorted(snap.review, key=lambda p: p.created_at):  # o que espera há mais tempo primeiro
        age = ago((now - datetime.fromisoformat(pr.created_at)).total_seconds(), lang)
        reviews.append(Entry(f"👀 {short_ref(pr)}  {_title(pr.title)} — {pr.author} · {age}", url=pr.url))
    out += _limit(reviews, lang) or [Entry(t("no_reviews", lang), header=True)]

    out.append(Entry(t("mine_header", lang, n=len(snap.mine)), header=True))
    key = lambda pr: (ORDER.index(status(pr, state)), -pr.number)  # noqa: E731
    mine = []
    for pr, depth in ordered(snap.mine, state.parent, key):
        indent = "    " * depth + ("↳ " if depth else "")
        emoji = EMOJI[status(pr, state)]
        text = f"{indent}{emoji} {short_ref(pr)}  {_title(pr.title)} — {_status_text(pr, state, lang)}"
        mine.append(Entry(text, url=pr.url))
    out += _limit(mine, lang) or [Entry(t("no_prs", lang), header=True)]
    return out
