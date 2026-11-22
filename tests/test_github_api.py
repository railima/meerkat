import json
from datetime import datetime, timezone
from pathlib import Path

from github_api import parse, search_queries

DATA = json.loads((Path(__file__).parent / "fixtures" / "graphql.json").read_text())


def test_parse_groups_and_fields():
    snap = parse(DATA)
    assert snap.viewer == "me"
    assert [p.number for p in snap.review] == [123]  # nó vazio ignorado
    assert [p.number for p in snap.mine] == [45]
    assert [p.number for p in snap.merged] == [44]

    review = snap.review[0]
    assert (review.repo, review.author, review.ci) == ("acme/api", "ana", "SUCCESS")

    mine = snap.mine[0]
    assert mine.ci is None
    assert mine.conflicting is True
    assert (mine.head, mine.base, mine.head_oid) == ("feat/pagamentos", "main", "m1")
    # Mais recente de outra pessoa: ignora o próprio review e o autor apagado (null).
    assert mine.last_feedback_at == "2026-11-19T15:00:00Z"

    assert snap.merged[0].merged_at == "2026-11-20T18:00:00Z"


def test_search_queries_use_seven_day_window():
    q = search_queries(datetime(2026, 11, 21, 12, tzinfo=timezone.utc))
    assert q["review"] == "is:open is:pr review-requested:@me archived:false"
    assert q["mine"] == "is:open is:pr author:@me archived:false"
    assert q["merged"] == "is:pr author:@me is:merged merged:>=2026-11-14"
