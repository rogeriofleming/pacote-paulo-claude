---
name: pesquisa-profunda
description: Pesquisa profunda multi-fonte com verificação adversarial, CHECKPOINT EM DISCO e retomada. Substitui a skill oficial deep-research (que dispara ~100 agentes, queima milhões de tokens e não salva nada em disco). Use quando pedirem "pesquisa profunda sobre X", "deep research de Y", "levanta com fontes cruzadas", e também "retoma/continua a pesquisa Z" — a retomada é parte desta skill. Se a pergunta estiver vaga, faça 2-3 esclarecimentos antes de rodar.
---

# Pesquisa Profunda — com checkpoint e retomada

Um harness de pesquisa multi-fonte próprio e editável, pensado para substituir a
`deep-research` oficial. **Nunca invoque a skill oficial `deep-research` nem o
workflow embutido de mesmo nome** — eles fazem a coisa errada (ver abaixo).

## Por que este harness existe

A `deep-research` oficial, num caso real, rodou 2× e produziu o pior cenário possível:

| Run | Agentes | Tokens | O que morreu |
|---|---|---|---|
| 1 | **100** | 1,5M | os 75 verificadores (25 claims × 3 votos) — 100% mortos por **limite de sessão** |
| 2 | **102** | 3,5M | timeout de 100s abandonou **18/25 vereditos válidos** (verificador legítimo leva minutos); síntese falhou |

E o pior: **nada em disco** → sessão morreu no limite → "retome daqui" não achava
nada → recomeçava do zero.

Este harness corrige as 5 causas: teto de agentes (~24, era ~100) · 1 verificador
cético em vez de 3 votos · **cada agente salva o próprio resultado em disco na
hora** · timeout largo como backstop (o limite real de trabalho vai no prompt) ·
guarda de budget antes das fases caras.

## Regras duras (invioláveis)

1. **RETOMADA ANTES DE RODAR:** se já existe uma pasta de resultados do mesmo tema
   (ver §Retomada), é PROIBIDO recomeçar do zero. Aproveite o que existe.
2. **Teto de escala:** os parâmetros do script (4 ângulos · 10 fontes · 8 vereditos)
   só aumentam se o usuário pedir explicitamente "pesquisa máxima" / "+tokens" — e
   mesmo assim no máximo 6/15/12.
3. **Pasta explícita:** sempre passe `pasta` apontando pro destino certo (ex.:
   `pesquisas/precos-mercado`). É lá que ficam fontes, vereditos e o `RELATORIO.md`.
4. **Ao receber o retorno do workflow:** confira que `<pasta>/RELATORIO.md` existe.
   Se a síntese falhou, o material está em `<pasta>/fontes/` — sintetize inline e
   ESCREVA o `RELATORIO.md` antes de responder. Nunca deixe o resultado só na conversa.
5. **Circuit breaker:** erro de limite/cota no meio → NÃO relance. Reporte o que já
   está salvo e o comando de retomada. Esperar o reset é decisão do usuário.
6. **Pesquisa rápida ≠ esta skill:** pergunta simples / fato pontual → faça 2-3
   buscas web inline, sem workflow nenhum.

## Como acionar

```
Workflow({
  scriptPath: ".claude/skills/pesquisa-profunda/scripts/deep_research.js",
  args: { pergunta: "<pergunta completa, com contexto/região/formato desejado>",
          pasta: "<onde salvar, ex.: pesquisas/precos-mercado>" }
})
```

O script salva sozinho, via agentes: `01_escopo.md`, `02_busca_N.md`,
`fontes/NN_host.md`, `vereditos/NN.md`, `RELATORIO.md` — tudo dentro de `pasta`.

## Retomada ("retoma/continua a pesquisa X") — NUNCA recomeçar sem estas 2 checagens

1. **Disco:** `ls <pasta>/` — fontes e relatório já salvos? Faltando só síntese →
   sintetize a partir dos arquivos. Faltando fontes → rode workflow novo SÓ dos
   ângulos/fontes que faltam (prompt ajustado), não tudo.
2. **Journal de runs antigos (mesmo de sessões mortas):** o resultado de todo run de
   workflow fica no diretório de sessão do Claude Code, em
   `~/.claude/projects/<projeto>/<sessão>/workflows/wf_*.json` (campo `result`, com
   claims e fontes). Busque por palavra-chave do tema:
   `grep -l "<palavra>" ~/.claude/projects/*/*/workflows/wf_*.json` → extraia o
   `result` e salve na `pasta`. Foi assim que uma pesquisa "perdida" foi recuperada
   inteira (20 fontes, 58 claims) sem gastar 1 token de busca.

Só depois dessas duas checagens, e declarando o que foi checado, é permitido rodar
busca nova — e só do que falta.

## Se estourar o limite no meio

Mensagem padrão: *"Limite atingido. Já estão salvos em `<pasta>`: X fontes, Y
vereditos. Nada se perdeu. Quando o limite resetar, diz 'continua a pesquisa
<tema>' que eu retomo do ponto exato."* — e NÃO relance nada até mandarem.

## As 5 fases do harness

1. **Scope** — decompõe a pergunta em 4 ângulos de busca complementares.
2. **Search** — 4 agentes WebSearch, um por ângulo.
3. **Fetch** — dedup de URL, fetch de até 10 fontes; cada agente SALVA a fonte em disco na hora.
4. **Verify** — até 8 claims centrais, 1 verificador cético cada (tenta refutar antes de aceitar).
5. **Synthesize** — síntese com citações; o agente ESCREVE o `RELATORIO.md` antes de retornar.
