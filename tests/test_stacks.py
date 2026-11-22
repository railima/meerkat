from stacks import analyze, ordered
from tests.test_model import make_pr


def test_child_of_open_parent_is_linked_and_remembered():
    a = make_pr(id="A", number=1, head="feat/a", base="main")
    b = make_pr(id="B", number=2, head="feat/b", base="feat/a", head_oid="b1")
    parent, rebase, memory = analyze([a, b], [], {})
    assert parent == {"B": "A"}
    assert rebase == {}
    assert memory == {"B": {"parent_id": "A", "parent_number": 1, "oid": "b1"}}


def test_parent_merged_and_child_retargeted_to_main_needs_rebase_until_push():
    memory = {"B": {"parent_id": "A", "parent_number": 1, "oid": "b1"}}
    merged_a = make_pr(id="A", number=1, head="feat/a", merged_at="2026-11-21T10:00:00Z")
    b = make_pr(id="B", number=2, head="feat/b", base="main", head_oid="b1")  # GitHub trocou a base

    parent, rebase, memory = analyze([b], [merged_a], memory)
    assert parent == {}
    assert rebase == {"B": 1}
    assert memory["B"]["parent_merged"] is True

    # O pai sai da janela de 7 dias, mas o filho continua precisando de rebase.
    _, rebase, memory = analyze([b], [], memory)
    assert rebase == {"B": 1}

    # Depois do push (novo commit), o aviso some e a memória é limpa.
    pushed = make_pr(id="B", number=2, head="feat/b", base="main", head_oid="b2")
    _, rebase, memory = analyze([pushed], [], memory)
    assert rebase == {}
    assert memory == {}


def test_parent_not_yet_in_merged_search_keeps_memory():
    memory = {"B": {"parent_id": "A", "parent_number": 1, "oid": "b1"}}
    b = make_pr(id="B", number=2, base="main", head_oid="b1")
    _, rebase, memory = analyze([b], [], memory)  # busca de mergeados ainda não indexou o pai
    assert rebase == {}
    assert "B" in memory


def test_base_still_pointing_to_merged_branch_needs_rebase():
    # Branch do pai não foi apagada: a base do filho continua "feat/a", mas sem PR aberto nela.
    memory = {"B": {"parent_id": "A", "parent_number": 1, "oid": "b1"}}
    merged_a = make_pr(id="A", number=1, head="feat/a")
    b = make_pr(id="B", number=2, base="feat/a", head_oid="b1")
    _, rebase, _ = analyze([b], [merged_a], memory)
    assert rebase == {"B": 1}


def test_gitflow_merged_release_does_not_flag_prs_on_develop():
    # PR de release develop -> main mergeado não é pai dos PRs abertos contra develop.
    release = make_pr(id="X", number=9, head="develop", base="main")
    b = make_pr(id="B", number=2, head="feat/b", base="develop")
    _, rebase, _ = analyze([b], [release], {})
    assert rebase == {}


def test_cross_repo_pr_is_never_a_parent():
    fork = make_pr(id="F", number=5, head="main", base="main", cross_repo=True)
    b = make_pr(id="B", number=2, head="feat/b", base="main")
    parent, _, memory = analyze([fork, b], [], {})
    assert parent == {}
    assert memory == {}


def test_conflict_needs_rebase_without_parent():
    _, rebase, _ = analyze([make_pr(id="C", conflicting=True)], [], {})
    assert rebase == {"C": None}


DAY = 86400


def test_missing_pr_memory_kept_within_ttl_and_dropped_after():
    memory = {"B": {"parent_id": "A", "parent_number": 1, "oid": "b1"}}
    # PR some da busca (atraso do índice ou limite de 50): a memória fica, marcada com a hora.
    _, _, memory = analyze([], [], memory, now=1000)
    assert memory["B"]["missing_since"] == 1000
    # Polls seguintes não reiniciam a contagem.
    _, _, memory = analyze([], [], memory, now=1000 + 6 * DAY)
    assert memory["B"]["missing_since"] == 1000
    # Passados 7 dias ausente, é descartada (PR fechado).
    _, _, memory = analyze([], [], memory, now=1000 + 7 * DAY + 1)
    assert memory == {}


def test_flag_restored_when_missing_pr_reappears():
    memory = {"B": {"parent_id": "A", "parent_number": 1, "oid": "b1", "parent_merged": True}}
    _, _, memory = analyze([], [], memory, now=1000)
    b = make_pr(id="B", number=2, base="main", head_oid="b1")
    _, rebase, memory = analyze([b], [], memory, now=2000)
    assert rebase == {"B": 1}
    assert "missing_since" not in memory["B"]


def test_ordered_puts_children_under_parent():
    a = make_pr(id="A", number=1)
    b = make_pr(id="B", number=2)
    c = make_pr(id="C", number=3)
    rows = ordered([c, b, a], {"B": "A"}, key=lambda p: p.number)
    assert [(p.id, depth) for p, depth in rows] == [("A", 0), ("B", 1), ("C", 0)]


def test_ordered_survives_cycles():
    a, b = make_pr(id="A"), make_pr(id="B")
    rows = ordered([a, b], {"A": "B", "B": "A"}, key=lambda p: p.id)
    assert sorted(p.id for p, _ in rows) == ["A", "B"]
