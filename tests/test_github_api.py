import io
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pytest

from github_api import AuthError, GitHubError, fetch, parse, search_queries

DATA = json.loads((Path(__file__).parent / "fixtures" / "graphql.json").read_text())


def test_parse_groups_and_fields():
    snap = parse(DATA)
    assert snap.viewer == "me"
    assert [p.number for p in snap.review] == [123]  # nó vazio ignorado
    assert [p.number for p in snap.mine] == [45]
    assert [p.number for p in snap.merged] == [44]

    review = snap.review[0]
    assert (review.repo, review.author, review.ci) == ("acme/api", "ana", "SUCCESS")
    assert review.cross_repo is True

    mine = snap.mine[0]
    assert mine.ci is None
    assert mine.conflicting is True
    assert mine.cross_repo is False
    assert (mine.head, mine.base, mine.head_oid) == ("feat/pagamentos", "main", "m1")
    # Mais recente de outra pessoa: ignora o próprio review, o autor apagado (null) e bots.
    assert mine.last_feedback_at == "2026-11-19T15:00:00Z"

    assert snap.merged[0].merged_at == "2026-11-20T18:00:00Z"


def test_search_queries_use_seven_day_window():
    q = search_queries(datetime(2026, 11, 21, 12, tzinfo=timezone.utc))
    assert q["review"] == "is:open is:pr review-requested:@me archived:false"
    assert q["mine"] == "is:open is:pr author:@me archived:false"
    assert q["merged"] == "is:pr author:@me is:merged merged:>=2026-11-14"


NOW = datetime(2026, 11, 21, 12, tzinfo=timezone.utc)


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TimeoutResponse(FakeResponse):
    def read(self, *a):
        raise TimeoutError("timed out")


def fake_urlopen(monkeypatch, result):
    def urlopen(request, timeout=None, context=None):
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)


def http_error(code):
    return urllib.error.HTTPError("https://api.github.com/graphql", code, "x", {}, None)


def body(obj):
    return FakeResponse(json.dumps(obj).encode())


def test_fetch_401_is_auth_error(monkeypatch):
    fake_urlopen(monkeypatch, http_error(401))
    with pytest.raises(AuthError):
        fetch("t", NOW)


def test_fetch_http_500_is_github_error(monkeypatch):
    fake_urlopen(monkeypatch, http_error(500))
    with pytest.raises(GitHubError) as e:
        fetch("t", NOW)
    assert not isinstance(e.value, AuthError)


def test_fetch_url_error_is_github_error(monkeypatch):
    fake_urlopen(monkeypatch, urllib.error.URLError("offline"))
    with pytest.raises(GitHubError):
        fetch("t", NOW)


def test_fetch_read_timeout_is_github_error(monkeypatch):
    fake_urlopen(monkeypatch, TimeoutResponse(b""))
    with pytest.raises(GitHubError):
        fetch("t", NOW)


def test_fetch_invalid_json_is_github_error(monkeypatch):
    fake_urlopen(monkeypatch, FakeResponse(b"<html>"))
    with pytest.raises(GitHubError):
        fetch("t", NOW)


def test_fetch_partial_errors_keep_data(monkeypatch):
    # Ex.: repositórios com SAML/SSO restrito geram erros, mas o resto da resposta vem.
    fake_urlopen(monkeypatch, body({"data": DATA, "errors": [{"message": "SAML"}]}))
    assert fetch("t", NOW) == DATA


def test_fetch_errors_without_data_is_github_error(monkeypatch):
    fake_urlopen(monkeypatch, body({"data": None, "errors": [{"message": "Bad query"}]}))
    with pytest.raises(GitHubError, match="Bad query"):
        fetch("t", NOW)
