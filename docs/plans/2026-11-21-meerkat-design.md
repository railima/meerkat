# Meerkat — design

Painel de PRs do GitHub na barra de menu (macOS) e na bandeja do sistema (Windows).

## Objetivo

Mostrar, sem abrir o navegador, o que precisa da atenção do usuário nos PRs do GitHub e avisar com notificações
do sistema quando algo muda: revisões pedidas, CI falhando, revisões recebidas e pilhas de stacked PRs que
precisam de rebase.

Fora do escopo: Azure DevOps, ações que alteram código ou o remoto (o Meerkat só avisa; nunca faz rebase ou push).

## Interface

**Ícone.** No macOS, o número de pendências aparece ao lado do ícone na barra de menu; no Windows, desenhado
sobre o ícone da bandeja. Sem pendências, ícone neutro. Pendências = revisões pedidas + PRs próprios com CI
falhando, mudanças pedidas ou rebase necessário. Com erro (sem rede, token inválido), o ícone ganha ⚠️.

**Menu.**

```
Precisam da sua revisão (2)
   👀 api#123  Ajusta cálculo de frete — ana · 3h
Meus PRs (4)
   ❌ api#45   Refatora pagamentos — CI falhou
      ↳ 🔁 api#46  Pix no checkout — rebase necessário (#45 mergeado)
   💬 web#90   Corrige layout mobile — mudanças pedidas
   ✅ psiu#12  i18n — aprovado
   🟡 psiu#13  Ícone novo — CI rodando
───────────────
Atualizado há 1 min · Atualizar agora
Pausar notificações por 1h
Iniciar com o sistema ✓
Configurações…
Sair
```

- Clique num PR abre no navegador.
- Filhos de pilha aparecem indentados sob o pai.
- Ordem: o que exige ação primeiro (❌ 💬 🔁), depois o que espera outros (🟡 ⏳ ✅ 📝).
- Status: ❌ CI falhou · 🟡 CI rodando · 💬 mudanças pedidas · ✅ aprovado · ⏳ aguardando revisão ·
  🔁 rebase necessário · 📝 rascunho.
- Inglês por padrão, com opção de português (como o Psiu).

**Notificações** (nativas): revisão pedida, CI falhou em PR próprio, PR próprio revisado (aprovado, mudanças
pedidas ou review/comentário novo de outra pessoa), pai de pilha mergeado. "Pausar por 1h" silencia as
notificações, mas o menu continua atualizando.

## Dados

**Autenticação.** Usa `gh auth token` se o GitHub CLI estiver logado. Senão, "Configurações…" abre uma caixa de
diálogo nativa (osascript no macOS, InputBox via PowerShell no Windows) para colar um token pessoal com escopo
`repo` (leitura). O token fica no Chaveiro do macOS / Gerenciador de Credenciais do Windows (`keyring`), nunca
em arquivo.

**Consulta.** Uma consulta GraphQL a cada 2 min (configurável: 1, 2, 5, 10) ou em "Atualizar agora", com três
buscas:

1. `is:open is:pr review-requested:@me archived:false`
2. `is:open is:pr author:@me archived:false` — com status do CI (`statusCheckRollup`), `reviewDecision`,
   `baseRefName`, `headRefName`, `headRefOid`, `mergeable`/`mergeStateStatus`, contagem de reviews e
   comentários por outras pessoas.
3. `is:pr author:@me is:merged merged:>=<últimos 7 dias>` — para detectar pais de pilha mergeados.

**Pilhas.** Entre os PRs abertos do usuário no mesmo repositório, se `base` de B = `head` de A, B é filho de A.
Como o GitHub costuma retargetar o filho para `main` quando o pai é mergeado e a branch apagada, o Meerkat guarda em
um arquivo local (`state.json`) a relação filho → pai e o `headRefOid` do filho. Quando o pai aparece como
mergeado, o filho fica 🔁 até seu `headRefOid` mudar (novo push). Conflito com a base (`mergeable = CONFLICTING`)
também marca 🔁.

**Eventos.** Cada busca é comparada com a anterior (snapshot em memória). A primeira busca após abrir o app só
registra o estado, sem notificar.

**Erros.** Falha de rede ou token inválido: ⚠️ no ícone, mensagem no menu, backoff progressivo até 10 min, sem
notificar o erro repetidamente.

## Estrutura

```
github_api.py   consulta GraphQL e conversão para objetos PR
stacks.py       árvore de pilhas e marcação de rebase necessário (puro)
events.py       diff entre snapshots → eventos de notificação (puro)
notifier.py     notificações nativas (winotify no Windows; Central de Notificações no macOS)
tray.py         ícone e menu (pystray + Pillow)
autostart.py    LaunchAgent (macOS) / chave Run do registro (Windows)
config.py       configurações em JSON (intervalo, idioma, pausa); token via keyring
i18n.py         textos em inglês e português
app.py          laço de atualização e ligação entre as partes
```

No macOS o app roda sem ícone no Dock (`LSUIElement`). Clicar numa notificação no macOS pode não abrir o PR
com o app sem assinatura da Apple; nesse caso o PR fica a um clique no menu.

## Testes

`pytest` com respostas da API em JSON de exemplo: conversão, montagem de pilhas (incluindo pai mergeado com o
filho já retargetado para `main`), eventos (nada na primeira busca, sem duplicar notificações, CI falhando só
notifica na transição). O CI roda os testes antes de empacotar.

## Distribuição

Repositório público novo (`railima/meerkat`, MIT), mesmo esquema do Psiu: PyInstaller, workflow que gera `.dmg` e
`.exe` a cada tag `v*` e publica uma Release. Mesmo cuidado com segredos: `.gitignore` reforçado e varredura
antes do primeiro push.
