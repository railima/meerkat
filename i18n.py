"""Textos do Meerkat em inglês (padrão) e português."""

STRINGS = {
    "en": {
        "review_header": "Needs your review ({n})",
        "mine_header": "My PRs ({n})",
        "no_reviews": "Nothing waiting for your review",
        "no_prs": "No open PRs",
        "more": "…and {n} more",
        "status_rebase": "rebase needed (#{parent} merged)",
        "status_conflict": "rebase needed (conflict)",
        "status_failing": "CI failed",
        "status_changes": "changes requested",
        "status_running": "CI running",
        "status_draft": "draft",
        "status_approved": "approved",
        "status_waiting": "awaiting review",
        "now": "now",
        "updated": "Updated {ago} ago",
        "updated_now": "Updated just now",
        "loading": "Loading…",
        "refresh": "Refresh now",
        "pause": "Pause notifications for 1h",
        "resume": "Resume notifications",
        "settings": "Settings",
        "interval": "Refresh every",
        "minutes": "{n} min",
        "language": "Language",
        "repos": "Watched repositories",
        "repos_empty": "(none yet)",
        "token": "GitHub token…",
        "token_prompt": "Paste a GitHub personal access token (repo scope, read-only).\n"
                        "Leave it empty to use your GitHub CLI login (gh).",
        "start_at_login": "Start at login",
        "quit": "Quit",
        "error_auth": "⚠️ GitHub login missing or invalid. Set a token in Settings.",
        "error_network": "⚠️ Can't reach GitHub ({detail})",
        "n_review_requested": "Review requested",
        "n_ci_failed": "CI failed",
        "n_approved": "PR approved",
        "n_changes_requested": "Changes requested",
        "n_commented": "New comment",
        "n_parent_merged": "Rebase needed",
        "n_body_review": "{pr} {title} — by {author}",
        "n_body_parent": "{pr} {title} — parent #{parent} was merged",
    },
    "pt-BR": {
        "review_header": "Precisam da sua revisão ({n})",
        "mine_header": "Meus PRs ({n})",
        "no_reviews": "Nada esperando sua revisão",
        "no_prs": "Nenhum PR aberto",
        "more": "…e mais {n}",
        "status_rebase": "rebase necessário (#{parent} mergeado)",
        "status_conflict": "rebase necessário (conflito)",
        "status_failing": "CI falhou",
        "status_changes": "mudanças pedidas",
        "status_running": "CI rodando",
        "status_draft": "rascunho",
        "status_approved": "aprovado",
        "status_waiting": "aguardando revisão",
        "now": "agora",
        "updated": "Atualizado há {ago}",
        "updated_now": "Atualizado agora",
        "loading": "Carregando…",
        "refresh": "Atualizar agora",
        "pause": "Pausar notificações por 1h",
        "resume": "Retomar notificações",
        "settings": "Configurações",
        "interval": "Atualizar a cada",
        "minutes": "{n} min",
        "language": "Idioma",
        "repos": "Repositórios vigiados",
        "repos_empty": "(nenhum ainda)",
        "token": "Token do GitHub…",
        "token_prompt": "Cole um token pessoal do GitHub (escopo repo, somente leitura).\n"
                        "Deixe vazio para usar o login do GitHub CLI (gh).",
        "start_at_login": "Iniciar com o sistema",
        "quit": "Sair",
        "error_auth": "⚠️ Login do GitHub ausente ou inválido. Configure um token.",
        "error_network": "⚠️ Sem conexão com o GitHub ({detail})",
        "n_review_requested": "Revisão pedida",
        "n_ci_failed": "CI falhou",
        "n_approved": "PR aprovado",
        "n_changes_requested": "Mudanças pedidas",
        "n_commented": "Comentário novo",
        "n_parent_merged": "Rebase necessário",
        "n_body_review": "{pr} {title} — por {author}",
        "n_body_parent": "{pr} {title} — o pai #{parent} foi mergeado",
    },
}

LANGUAGES = {"en": "English", "pt-BR": "Português"}


def t(key, lang, **values):
    return STRINGS.get(lang, STRINGS["en"])[key].format(**values)


def short_ref(pr):
    """"acme/api" + 46 -> "api#46"."""
    return f"{pr.repo.split('/')[-1]}#{pr.number}"


def ago(seconds, lang):
    seconds = max(0, int(seconds))
    if seconds < 60:
        return t("now", lang)
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def notification(event, lang):
    pr = event.pr
    title = t(f"n_{event.kind}", lang)
    if event.kind == "parent_merged":
        body = t("n_body_parent", lang, pr=short_ref(pr), title=pr.title, parent=event.parent)
    elif event.kind == "review_requested":
        body = t("n_body_review", lang, pr=short_ref(pr), title=pr.title, author=pr.author)
    else:
        body = f"{short_ref(pr)} {pr.title}"
    return title, body
