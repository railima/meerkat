"""Pilhas de stacked PRs: quem é filho de quem e quem precisa de rebase."""

from collections import defaultdict


def analyze(mine, merged, memory):
    """Retorna (parent, rebase, nova_memoria).

    parent: id do PR -> id do pai aberto.
    rebase: id do PR -> número do pai mergeado, ou None quando o motivo é conflito.
    memória: id do filho -> {"parent_id", "parent_number", "oid", "parent_merged"?}. Guarda quem era o pai
    porque o GitHub costuma trocar a base do filho para main quando o pai é mergeado.
    """
    open_by_head = {(p.repo, p.head): p for p in mine}
    merged_by_head = {(p.repo, p.head): p for p in merged}
    merged_ids = {p.id for p in merged}
    parent, rebase, new_memory = {}, {}, {}

    for pr in mine:
        entry = memory.get(pr.id)
        open_parent = open_by_head.get((pr.repo, pr.base))
        if open_parent and open_parent.id != pr.id:
            parent[pr.id] = open_parent.id
            new_memory[pr.id] = {"parent_id": open_parent.id, "parent_number": open_parent.number, "oid": pr.head_oid}
        elif entry and pr.head_oid == entry["oid"]:
            # Pai não está mais aberto e o filho não recebeu push desde então.
            entry = {**entry, "parent_merged": entry.get("parent_merged") or entry["parent_id"] in merged_ids}
            new_memory[pr.id] = entry
            if entry["parent_merged"]:
                rebase[pr.id] = entry["parent_number"]

        merged_parent = merged_by_head.get((pr.repo, pr.base))
        if merged_parent:  # a base ainda aponta para a branch do pai já mergeado
            rebase[pr.id] = merged_parent.number
        if pr.id not in rebase and pr.conflicting:
            rebase[pr.id] = None

    return parent, rebase, new_memory


def ordered(mine, parent, key):
    """Lista (pr, profundidade) com cada filho logo abaixo do pai; raízes e irmãos ordenados por `key`."""
    ids = {p.id for p in mine}
    children, roots = defaultdict(list), []
    for pr in mine:
        p = parent.get(pr.id)
        (children[p] if p in ids else roots).append(pr)

    rows, seen = [], set()

    def walk(pr, depth):
        if pr.id in seen:
            return
        seen.add(pr.id)
        rows.append((pr, depth))
        for child in sorted(children[pr.id], key=key):
            walk(child, depth + 1)

    for root in sorted(roots, key=key):
        walk(root, 0)
    for pr in sorted(mine, key=key):  # PRs presos em ciclo (sem raiz) não podem sumir
        walk(pr, 0)
    return rows
