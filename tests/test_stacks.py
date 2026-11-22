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
    merged_a = make_pr(id="A", number=1, head="feat/a")
    b = make_pr(id="B", number=2, base="feat/a")
    _, rebase, _ = analyze([b], [merged_a], {})
    assert rebase == {"B": 1}


def test_conflict_needs_rebase_without_parent():
    _, rebase, _ = analyze([make_pr(id="C", conflicting=True)], [], {})
    assert rebase == {"C": None}


def test_closed_prs_are_dropped_from_memory():
    _, _, memory = analyze([], [], {"B": {"parent_id": "A", "parent_number": 1, "oid": "b1"}})
    assert memory == {}


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
