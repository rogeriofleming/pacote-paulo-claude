---
name: iniciar-sessao
description: Executa o protocolo de início de sessão. Descobre a data/hora reais, sincroniza o git (e integra branches de sessões feitas pelo celular), lê os documentos de estado do projeto (CLAUDE.md, WORKFLOW.md, PROXIMA_SESSAO.md), entende o que está pendente e reporta o estado atual + a próxima ação. Use sempre no início de uma conversa de trabalho num projeto.
---

# Protocolo de Início de Sessão

Execute em ordem, sem pular etapas. (Adapte os nomes de arquivo/fuso à sua realidade —
esta skill assume o padrão CLAUDE.md + WORKFLOW.md + PROXIMA_SESSAO.md, mas o método
vale pra qualquer conjunto de docs de estado.)

## 00. Saber a DATA e HORA reais — SEMPRE, primeira coisa

- Rodar: `date "+%Y-%m-%d %H:%M (%A)"` (ajuste o fuso com `TZ="Area/Cidade"` se precisar).
- No Windows o `TZ` às vezes não pega e o `date` volta em UTC — nesse caso converta pro
  seu fuso à mão antes de seguir.
- **Gravar a data/hora e usá-la em TODA a sessão** — datar tarefas, interpretar
  "hoje/amanhã/ontem", checar prazos vencidos. Nunca chutar a data. Se uma conta de data
  não fechar, refazer o `date`, não inferir.

## 0. Sincronizar com o GitHub (se o projeto for um repo git)

- Verificar se existe `.git/` na raiz. Se sim, na raiz do projeto:
  ```
  git pull --rebase --autostash origin master
  ```
- "Already up to date." ou commits novos → seguir (o estado mais novo já está nos arquivos).
- Conflito ou erro → **PARAR**, mostrar o erro e perguntar como resolver. Não resolver sozinho.
- Não é git → pular em silêncio.

## 0.5. Checar branches de sessões feitas pelo celular / web

Sessões via `claude.ai/code` (celular) caem numa **branch isolada** (`claude/session-*`),
nunca no master. Integrar quando achar:

- `git fetch --all --prune` e `git branch -r --no-merged master`.
- Inspecionar: `git log --oneline master..origin/<branch>` + `git diff --stat master origin/<branch>` + `git merge-base master origin/<branch>`.
- **Fast-forward** (merge-base == HEAD do master) → `git merge --ff-only origin/<branch>` + push. Fazer sozinho.
- **Merge real só em docs de estado** (WORKFLOW/PROXIMA_SESSAO, com `merge=union`) e nada quebra → fazer e sinalizar no reporte.
- **Toca código OU risco de perder trabalho** → **PARAR e perguntar**, mostrando o diff dos dois lados.
- Integrada no master → apagar a branch: `git push origin --delete <branch>`.
- Sinalizar no reporte: "integrei a sessão de celular X" ou "tem branch Y que precisa de decisão".

## 1-4. Ler os documentos de estado

1. **CLAUDE.md** — identidade, papel e regras de operação do projeto.
2. **WORKFLOW.md** — o estado atual: o que está no ar, o que está pendente/em andamento.
3. **PROXIMA_SESSAO.md** (se existir) — o contexto que a sessão anterior deixou.
4. **Briefing/plano do trabalho ativo** (se houver) — o que está sendo construído.

Só carregue os conhecimentos/skills que a tarefa da vez exige — não tudo de uma vez.

## Output esperado — o reporte

Reportar de forma **enxuta**: data/hora → estado do projeto → próxima ação. Nada de
despejar a lista inteira de comandos disponíveis (lota a tela e não ajuda).

**Formato (copiar e preencher):**
```
═══════════════════════════════════════
  Sessão iniciada
  📅 [dia-da-semana], DD/MM/AAAA · HH:MM
═══════════════════════════════════════

Projeto ativo: [Nome]
Status: [O que está pronto e o que está pendente]
Próxima ação: [O que fazer agora]

═══════════════════════════════════════
```

> A data/hora (da etapa 00) entra no cabeçalho — é a prova de que a sessão sabe em que
> dia está. Sem ela, o reporte está incompleto.

> **Dica:** se você gosta de um ritual de abertura (uma intenção, uma oração, um foco do
> dia), este é o lugar — coloque-o no topo do reporte. É opcional e pessoal; adapte ou
> remova à vontade.
