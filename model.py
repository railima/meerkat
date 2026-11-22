"""Estruturas de dados do Meerkat e o status de cada PR."""

from dataclasses import dataclass, field

FAILING = {"FAILURE", "ERROR"}
RUNNING = {"PENDING", "EXPECTED"}

# Ordem de exibição: primeiro o que exige ação do usuário.
ORDER = ["rebase", "failing", "changes", "running", "draft", "approved", "waiting"]
ATTENTION = {"rebase", "failing", "changes"}


@dataclass(frozen=True)
class PR:
    id: str
    repo: str  # "dono/nome"
    number: int
    title: str
    url: str
    author: str
    draft: bool
    created_at: str
    merged_at: str | None
    head: str
    base: str
    head_oid: str
    ci: str | None  # SUCCESS, FAILURE, ERROR, PENDING, EXPECTED ou None (sem checks)
    review_decision: str | None  # APPROVED, CHANGES_REQUESTED, REVIEW_REQUIRED ou None
    conflicting: bool
    last_feedback_at: str | None  # review ou comentário mais recente de outra pessoa (ISO 8601)


@dataclass(frozen=True)
class Snapshot:
    viewer: str
    review: tuple  # PRs que pedem a revisão do usuário
    mine: tuple  # PRs abertos do usuário
    merged: tuple  # PRs do usuário mergeados recentemente


@dataclass
class State:
    snapshot: Snapshot
    parent: dict = field(default_factory=dict)  # id do PR -> id do PR pai (aberto)
    rebase: dict = field(default_factory=dict)  # id do PR -> número do pai mergeado, ou None (conflito)


def status(pr, state):
    """Retorna o status do PR; a ordem das checagens é a prioridade de exibição.

    "rebase" vem de `State.rebase`, que stacks.analyze preenche tanto para pai mergeado quanto para conflito.
    """
    if pr.id in state.rebase:
        return "rebase"
    if pr.ci in FAILING:
        return "failing"
    if pr.review_decision == "CHANGES_REQUESTED":
        return "changes"
    if pr.ci in RUNNING:
        return "running"
    if pr.draft:
        return "draft"
    if pr.review_decision == "APPROVED":
        return "approved"
    return "waiting"


def attention_count(state):
    """Conta revisões pedidas ao usuário mais os PRs dele que exigem ação (rebase, failing, changes)."""
    mine = sum(1 for pr in state.snapshot.mine if status(pr, state) in ATTENTION)
    return len(state.snapshot.review) + mine
