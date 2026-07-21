---
name: encerrar-sessao
description: Executa o protocolo de encerramento de sessão. Não é só anotar o que foi feito — é COLHER a sessão inteira: relê a conversa, extrai aprendizados (feedback→memória, conhecimento→doc, trabalho extraordinário→skill), garante FONTE ÚNICA de cada informação, atualiza os docs de estado (WORKFLOW.md/PROXIMA_SESSAO.md), arquiva um resumo se a sessão foi pesada e sincroniza o git. Use ao final de qualquer sessão de trabalho.
---

# Protocolo de Encerramento de Sessão

> Encerrar sessão **não é faxina, é colheita.** Uma sessão inteira gera aprendizado — se
> ele não for capturado e roteado pro lugar único e certo, foi desperdiçado. Executar
> TODOS os passos, em ordem. Nenhum é opcional só porque "a sessão foi pequena" (aí os
> passos ficam curtos, mas rodam).

## ⚖️ As duas leis que regem este protocolo

1. **UMA informação, UM documento (fonte única).** Antes de gravar qualquer coisa,
   verificar se ela já existe em outro doc (`grep`). Se existe → **consolidar num só lugar
   e apontar pra ele**, nunca criar segunda cópia. Informação duplicada dessincroniza e
   vira mentira na sessão seguinte.
2. **Depoimento do usuário é FATO.** "Já fiz / editei / concluí X" → atualizar TODOS os
   docs de status na hora (varrer com `grep`, não só o que está à vista). Nunca deixar um
   doc falando como se estivesse pendente.

---

## 1. RELER a conversa inteira da sessão — a colheita

Antes de escrever qualquer coisa, revisar tudo o que passou na sessão (não só a última
tarefa). Para cada item relevante, decidir o DESTINO ÚNICO:

| O que apareceu na conversa | Vai pra (fonte única) |
|---|---|
| Correção/preferência sobre **como o agente deve agir** | **Memória** `type: feedback` (+ linha no índice de memórias) |
| Fato novo sobre **o usuário / pessoas / projeto** (não derivável do código) | **Memória** `type: user`/`project`; se for grande, doc de conhecimento e a memória aponta pra ele |
| **Conhecimento técnico/conceitual** reutilizável | Doc de conhecimento — o lugar único daquele tema |
| **Trabalho extraordinário / processo novo** que vale repetir | **Vira skill** → acionar a skill de criar skill |
| Caminho técnico percorrido (erros, descartes, reescritas) | `processo_[tarefa].md` |
| Mudança de **status** de produto/tarefa | A fonte única de status (WORKFLOW.md) — e só ela |

**Gatilho de skill:** se nesta sessão resolvi algo difícil com um método que vou querer
repetir, OU o usuário pediu a mesma coisa de um jeito que dá pra automatizar → candidato a
skill. Propor antes de criar.

**Gatilho de memória:** se o usuário corrigiu, ensinou, cravou uma regra, ou revelou algo
dele/das pessoas → memória AGORA, com o "Why" e o "How to apply".

## 2. Garantir FONTE ÚNICA (anti-duplicação)

Para cada informação gravada no passo 1: rodar `grep` pelo dado no projeto. Achou a mesma
info em outro doc? Escolher **o lar definitivo**, deixar a versão certa só lá, e nos outros
trocar por um ponteiro ("ver X"). Reportar o que foi consolidado.

> **Se você mantém um painel/dashboard que espelha dados que têm dono:** ele pode ter
> dessincronizado durante a sessão. Vale um passo de verificação (manual ou por script)
> comparando o valor espelhado com o doc-dono, e um conserto antes de fechar.

## 2.5. Rede de notas (se você usa Obsidian ou wikilinks) — opcional

Se o seu projeto liga documentos por `[[links]]`, para CADA doc criado/tocado na sessão,
confira com grep:

- **Entrada** — alguém aponta pra ele? `grep -rlF "[[nome-do-doc]]" --include="*.md" .`
  (o `-F` é obrigatório: sem ele os colchetes viram classe de caracteres). Zero = órfão →
  linkar do doc-pai natural (índice, hub, plano ou doc que o mencionou).
- **Saída** — ele aponta pra alguém? `grep "\[\[" <arquivo>`. Zero = beco sem saída →
  linkar o que ele tocou. *Exceção: um índice pode ser nó-raiz (só entradas).*

Falhou → linkar AGORA (2 min), nunca virar pendência. Doc órfão hoje = sessão de limpeza
semana que vem.

## 3. Atualizar WORKFLOW.md — é ESTADO, não diário ⚠️ HIGIENE ANTI-INCHAÇO

O WORKFLOW.md vivo mostra **só o que está PENDENTE ou EM ANDAMENTO** + o status atual dos
produtos (fonte única de status). Histórico vai pro `WORKFLOW_arquivo.md`.

- Marcar concluídas ✅ · atualizar status.
- **Cabeçalho:** nova linha `> Atualizado em: …` no topo, empurra a anterior pra
  `> _Anterior_`. Passou de ~3 linhas de sessão no topo → move a mais antiga pro arquivo.
- **NUNCA** criar seção "✅ Entregue na sessão N" no WORKFLOW vivo (isso vai pro resumo de
  sessão, passo 4).
- **Checagem final:** se o WORKFLOW passou de um tamanho saudável (ex.: ~350 linhas) →
  arquivar até voltar ao normal (`wc -l WORKFLOW.md`).

> **Padrão útil — cada coisa tem UM dono.** Se você separa "tarefas suas" de "status de
> produto" de "trabalho de sessão", mantenha cada tipo em UM doc só e nos outros só um
> ponteiro. Repetir a mesma pendência em 3 docs é a receita de um deles ficar velho e você
> cobrar/relatar algo que já foi feito.

## 4. Arquivar RESUMO da sessão — se a sessão foi pesada

Se muita coisa aconteceu (várias entregas, decisões, aprendizados), escrever
`sessoes/sessao_NN_AAAA-MM-DD.md`:

- `NN` = próximo número (checar o último em `sessoes/` e no `PROXIMA_SESSAO.md`; incrementar).
- Conteúdo: o que foi feito · decisões tomadas · aprendizados colhidos (com link pras
  memórias/skills geradas) · pendências que sobraram.
- É **arquivo histórico** — nasce e nunca mais muda. Não confundir com PROXIMA_SESSAO.md.

Sessão leve (1-2 coisas) → pular o resumo, mas registrar o essencial no WORKFLOW.

## 5. Escrever PROXIMA_SESSAO.md — sobrescreve, nunca empilha

Só o relevante pra próxima sessão: `Data desta sessão` (com nº) · **o trabalho de sessão
(a esteira do que fazer)** · `Contexto importante` (decisões/bloqueios/gotchas) ·
`Primeira ação recomendada`. É de uma sessão só — SEMPRE sobrescreve.

- ⚠️ **Perigo da cópia herdada:** este arquivo é reescrito a cada sessão copiando o
  anterior. **Cada item que você mantiver, confira contra o dono ANTES** (`git fetch`
  primeiro). Item que você não conferiu = item que não entra. (Já aconteceu de uma esteira
  "ressuscitar" uma tarefa dias depois de ela estar pronta, só por herdar o texto sem conferir.)

## 6. Limpar /tmp/

Deletar temporários da sessão. Mover pra pasta definitiva só o que for referência futura.

## 7. Sincronizar o git

Fazer commit + push do que mudou. Se houver **sessões paralelas** (outra máquina, celular),
prefira commit atômico por arquivo (evite `git add -A` cego) e rode `git fetch` antes de
afirmar qualquer estado. Erro de push (rede/auth/conflito) → **avisar no reporte, nunca
silenciar**.

## 8. Reportar

- 2-3 linhas do que foi feito.
- **A colheita:** memórias criadas · conhecimentos gravados · skills propostas/criadas ·
  consolidações de fonte única feitas.
- Confirmar WORKFLOW.md + (processo/resumo se houve) + PROXIMA_SESSAO.md atualizados.
- Confirmar sync (ou reportar o erro).
