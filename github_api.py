"""Busca os PRs no GitHub (uma consulta GraphQL) e converte a resposta em objetos PR."""

import json
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import timedelta
from pathlib import Path

import certifi

from model import PR, Snapshot

API_URL = "https://api.github.com/graphql"
# Onde o GitHub CLI costuma estar quando o app é aberto fora do terminal (sem o PATH do shell).
GH_PATHS = ["/opt/homebrew/bin/gh", "/usr/local/bin/gh", r"C:\Program Files\GitHub CLI\gh.exe"]

QUERY = """
query($review: String!, $mine: String!, $merged: String!) {
  viewer { login }
  review: search(query: $review, type: ISSUE, first: 50) { nodes { ...pr } }
  mine: search(query: $mine, type: ISSUE, first: 50) { nodes { ...pr } }
  merged: search(query: $merged, type: ISSUE, first: 50) { nodes { ...pr } }
}
fragment pr on PullRequest {
  id number title url isDraft createdAt mergedAt state
  headRefName baseRefName headRefOid mergeable reviewDecision
  author { login }
  repository { nameWithOwner }
  commits(last: 1) { nodes { commit { statusCheckRollup { state } } } }
  reviews(last: 20) { nodes { author { login } submittedAt } }
  comments(last: 20) { nodes { author { login } createdAt } }
}
"""


class GitHubError(Exception):
    pass


class AuthError(GitHubError):
    pass


def search_queries(now):
    since = (now - timedelta(days=7)).date().isoformat()
    return {
        "review": "is:open is:pr review-requested:@me archived:false",
        "mine": "is:open is:pr author:@me archived:false",
        "merged": f"is:pr author:@me is:merged merged:>={since}",
    }


def fetch(token, now):
    body = json.dumps({"query": QUERY, "variables": search_queries(now)}).encode()
    request = urllib.request.Request(API_URL, data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "meerkat",
    })
    # certifi: o Python empacotado nem sempre acha os certificados do sistema.
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(request, timeout=30, context=context) as response:
            data = json.load(response)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise AuthError("401") from e
        raise GitHubError(f"HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise GitHubError(str(e.reason)) from e
    if data.get("errors"):
        raise GitHubError(data["errors"][0].get("message", "GraphQL error"))
    return data["data"]


def _latest_feedback(node, viewer):
    times = [
        item.get("submittedAt") or item.get("createdAt")
        for conn in (node["reviews"], node["comments"])
        for item in conn["nodes"]
        if item.get("author") and item["author"]["login"] != viewer
    ]
    return max((t for t in times if t), default=None)


def _pr(node, viewer):
    commits = node["commits"]["nodes"]
    rollup = commits[0]["commit"]["statusCheckRollup"] if commits else None
    return PR(
        id=node["id"],
        repo=node["repository"]["nameWithOwner"],
        number=node["number"],
        title=node["title"],
        url=node["url"],
        author=(node.get("author") or {}).get("login", "ghost"),
        draft=node["isDraft"],
        created_at=node["createdAt"],
        merged_at=node.get("mergedAt"),
        head=node["headRefName"],
        base=node["baseRefName"],
        head_oid=node["headRefOid"],
        ci=rollup["state"] if rollup else None,
        review_decision=node.get("reviewDecision"),
        conflicting=node.get("mergeable") == "CONFLICTING",
        last_feedback_at=_latest_feedback(node, viewer),
    )


def parse(data):
    viewer = data["viewer"]["login"]

    def prs(key):
        return tuple(_pr(n, viewer) for n in data[key]["nodes"] if n and n.get("id"))

    return Snapshot(viewer=viewer, review=prs("review"), mine=prs("mine"), merged=prs("merged"))


def gh_cli_token():
    """Token do GitHub CLI (`gh auth token`), se instalado e logado."""
    exe = shutil.which("gh") or next((p for p in GH_PATHS if Path(p).exists()), None)
    if not exe:
        return None
    flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
    try:
        result = subprocess.run([exe, "auth", "token"], capture_output=True, text=True, timeout=10, **flags)
    except (OSError, subprocess.TimeoutExpired):
        return None
    token = result.stdout.strip()
    return token if result.returncode == 0 and token else None
