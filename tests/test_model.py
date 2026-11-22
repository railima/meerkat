from model import PR, Snapshot, State, attention_count, status


def make_pr(**kw):
    base = dict(
        id="PR_1", repo="acme/api", number=1, title="T", url="https://github.com/acme/api/pull/1",
        author="ana", draft=False, created_at="2026-11-20T10:00:00Z", merged_at=None,
        head="feat/a", base="main", head_oid="aaa", ci="SUCCESS", review_decision=None,
        conflicting=False, last_feedback_at=None, cross_repo=False,
    )
    base.update(kw)
    return PR(**base)


def state(mine=(), review=(), rebase=None):
    return State(Snapshot("me", tuple(review), tuple(mine), ()), parent={}, rebase=rebase or {})


def test_status_priority():
    s = state(rebase={"PR_9": 3})
    assert status(make_pr(id="PR_9", ci="FAILURE"), s) == "rebase"
    assert status(make_pr(ci="FAILURE", review_decision="CHANGES_REQUESTED"), s) == "failing"
    assert status(make_pr(ci="ERROR"), s) == "failing"
    assert status(make_pr(review_decision="CHANGES_REQUESTED"), s) == "changes"
    assert status(make_pr(ci="PENDING"), s) == "running"
    assert status(make_pr(draft=True), s) == "draft"
    assert status(make_pr(review_decision="APPROVED"), s) == "approved"
    assert status(make_pr(), s) == "waiting"
    assert status(make_pr(ci="EXPECTED"), s) == "running"
    assert status(make_pr(ci=None), s) == "waiting"
    assert status(make_pr(draft=True, review_decision="APPROVED"), s) == "draft"
    assert status(make_pr(id="x"), state(rebase={"x": None})) == "rebase"


def test_attention_count_includes_reviews_and_actionable_prs():
    mine = [make_pr(id="a", ci="FAILURE"), make_pr(id="b"), make_pr(id="c", review_decision="CHANGES_REQUESTED")]
    s = state(mine=mine, review=[make_pr(id="r1"), make_pr(id="r2")])
    assert attention_count(s) == 4
    assert attention_count(state(mine=[make_pr(id="x")], rebase={"x": None})) == 1


def test_without_repos_drops_muted_repositories():
    from model import without_repos

    snap = Snapshot("me", (make_pr(id="r", repo="a/x"),), (make_pr(id="m1", repo="a/x"), make_pr(id="m2", repo="b/y")),
                    (make_pr(id="g", repo="b/y"),))
    filtered = without_repos(snap, {"b/y"})
    assert [p.id for p in filtered.review] == ["r"]
    assert [p.id for p in filtered.mine] == ["m1"]
    assert filtered.merged == ()
    assert filtered.viewer == "me"
    assert without_repos(snap, set()) == snap
