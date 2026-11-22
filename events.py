"""Compara dois estados e decide o que notificar."""

from dataclasses import dataclass

from model import FAILING, PR


@dataclass(frozen=True)
class Event:
    kind: str  # review_requested, ci_failed, approved, changes_requested, commented, parent_merged
    pr: PR
    parent: int | None = None  # número do pai mergeado (parent_merged)


def diff(prev, cur):
    if prev is None:
        return []  # primeira busca: só registra o estado atual
    events = []

    seen = {p.id for p in prev.snapshot.review}
    events += [Event("review_requested", p) for p in cur.snapshot.review if p.id not in seen]

    old_mine = {p.id: p for p in prev.snapshot.mine}
    for pr in cur.snapshot.mine:
        old = old_mine.get(pr.id)
        if pr.ci in FAILING and (old is None or old.ci not in FAILING):
            events.append(Event("ci_failed", pr))
        if old:
            if pr.review_decision != old.review_decision and pr.review_decision == "APPROVED":
                events.append(Event("approved", pr))
            elif pr.review_decision != old.review_decision and pr.review_decision == "CHANGES_REQUESTED":
                events.append(Event("changes_requested", pr))
            elif pr.last_feedback_at and (not old.last_feedback_at or pr.last_feedback_at > old.last_feedback_at):
                # Só feedback mais novo: se o último comentário for apagado, o anterior não notifica de novo.
                events.append(Event("commented", pr))
        parent = cur.rebase.get(pr.id)
        # Exige o PR no estado anterior: se ele sumiu da busca e voltou, o aviso já foi dado.
        if old and parent is not None and prev.rebase.get(pr.id) != parent:
            events.append(Event("parent_merged", pr, parent))
    return events
