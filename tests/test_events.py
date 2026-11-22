from events import diff
from model import Snapshot, State
from tests.test_model import make_pr


def st(review=(), mine=(), rebase=None):
    return State(Snapshot("me", tuple(review), tuple(mine), ()), parent={}, rebase=rebase or {})


def kinds(events):
    return [(e.kind, e.pr.id) for e in events]


def test_first_snapshot_never_notifies():
    assert diff(None, st(review=[make_pr(id="R")], mine=[make_pr(id="M", ci="FAILURE")])) == []


def test_new_review_request():
    assert kinds(diff(st(), st(review=[make_pr(id="R")]))) == [("review_requested", "R")]
    assert diff(st(review=[make_pr(id="R")]), st(review=[make_pr(id="R")])) == []


def test_ci_failure_only_on_transition():
    prev = st(mine=[make_pr(id="M", ci="PENDING")])
    cur = st(mine=[make_pr(id="M", ci="FAILURE")])
    assert kinds(diff(prev, cur)) == [("ci_failed", "M")]
    assert diff(cur, cur) == []


def test_review_decisions_and_comments():
    base = make_pr(id="M")
    assert kinds(diff(st(mine=[base]), st(mine=[make_pr(id="M", review_decision="APPROVED",
                                                         last_feedback_at="2026-11-21T10:00:00Z")]))) \
        == [("approved", "M")]
    assert kinds(diff(st(mine=[base]), st(mine=[make_pr(id="M", review_decision="CHANGES_REQUESTED")]))) \
        == [("changes_requested", "M")]
    assert kinds(diff(st(mine=[base]), st(mine=[make_pr(id="M", last_feedback_at="2026-11-21T10:00:00Z")]))) \
        == [("commented", "M")]


def test_parent_merged_once():
    pr = make_pr(id="B")
    prev, cur = st(mine=[pr]), st(mine=[pr], rebase={"B": 7})
    events = diff(prev, cur)
    assert kinds(events) == [("parent_merged", "B")]
    assert events[0].parent == 7
    assert diff(cur, cur) == []
    assert diff(prev, st(mine=[pr], rebase={"B": None})) == []  # conflito não notifica


def test_older_feedback_does_not_notify():
    # Ex.: o comentário mais recente foi apagado e o anterior volta a ser o último.
    prev = st(mine=[make_pr(id="M", last_feedback_at="2026-11-21T10:00:00Z")])
    cur = st(mine=[make_pr(id="M", last_feedback_at="2026-11-20T10:00:00Z")])
    assert diff(prev, cur) == []


def test_parent_merged_not_repeated_when_pr_reappears():
    # PR sumiu da busca por um poll e voltou: o aviso de pai mergeado já foi dado antes.
    pr = make_pr(id="B")
    assert diff(st(), st(mine=[pr], rebase={"B": 7})) == []
