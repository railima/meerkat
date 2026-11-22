from datetime import datetime, timezone

from menu import Entry, entries
from model import Snapshot, State
from tests.test_model import make_pr

NOW = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)


def test_sections_order_and_nesting():
    review = [make_pr(id="R", repo="acme/api", number=123, title="Ajusta frete", author="ana",
                      created_at="2026-11-21T09:00:00Z")]
    a = make_pr(id="A", number=45, title="Refatora pagamentos", ci="FAILURE", head="feat/a")
    b = make_pr(id="B", number=46, title="Pix", base="feat/a")
    c = make_pr(id="C", repo="acme/web", number=90, title="Layout", review_decision="APPROVED")
    state = State(Snapshot("me", tuple(review), (c, b, a), ()), parent={"B": "A"}, rebase={"B": 44})

    rows = entries(state, NOW, "en")
    assert rows == [
        Entry("Needs your review (1)", header=True),
        Entry("👀 api#123  Ajusta frete — ana · 3h", url=review[0].url),
        Entry("My PRs (3)", header=True),
        Entry("❌ api#45  Refatora pagamentos — CI failed", url=a.url),
        Entry("    ↳ 🔁 api#46  Pix — rebase needed (#44 merged)", url=b.url),
        Entry("✅ web#90  Layout — approved", url=c.url),
    ]


def test_empty_sections_and_long_titles():
    state = State(Snapshot("me", (), (), ()))
    assert entries(state, NOW, "pt-BR") == [
        Entry("Precisam da sua revisão (0)", header=True),
        Entry("Nada esperando sua revisão", header=True),
        Entry("Meus PRs (0)", header=True),
        Entry("Nenhum PR aberto", header=True),
    ]
    long = make_pr(title="x" * 80)
    rows = entries(State(Snapshot("me", (), (long,), ())), NOW, "en")
    assert "x" * 55 + "…" in rows[-1].text
