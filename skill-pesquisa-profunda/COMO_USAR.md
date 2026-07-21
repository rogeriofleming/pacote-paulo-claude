# Como instalar e usar a Pesquisa Profunda

## O que é

Um harness de **pesquisa multi-fonte com verificação** — pensado pra substituir a
skill `deep-research` oficial do Claude Code, que tem um defeito sério: dispara ~100
subagentes, queima milhões de tokens e **não salva nada em disco**, então se a sessão
morre no meio (limite/timeout) você perde tudo e recomeça do zero.

Este harness faz o oposto:

- **Teto duro de ~24 agentes** (era ~100).
- **Cada agente salva o próprio resultado em disco na hora** — a sessão pode morrer
  que nada se perde.
- **1 verificador cético por claim** (que tenta refutar antes de aceitar), em vez de
  3 votos redundantes.
- **Retomada real:** "continua a pesquisa X" reaproveita o que já está salvo em vez
  de rodar tudo de novo.

Ele roda em 5 fases: decompor a pergunta em ângulos → buscar na web → puxar e extrair
as fontes → verificar os claims centrais → sintetizar num `RELATORIO.md` com citações.

## Instalação

1. Copie a pasta inteira pra `.claude/skills/pesquisa-profunda/` na raiz do seu projeto:
   ```
   .claude/skills/pesquisa-profunda/SKILL.md
   .claude/skills/pesquisa-profunda/scripts/deep_research.js
   ```
2. Pronto — o Claude Code carrega a skill automaticamente a partir dessa pasta.

> **Requisito:** o script usa o harness de workflows/subagentes do Claude Code
> (`Workflow`, `agent`, `pipeline`, `parallel`) e as ferramentas `WebSearch`/`WebFetch`.
> Precisa de um ambiente Claude Code que tenha essas ferramentas habilitadas.

## Como acionar

Diga "pesquisa profunda sobre X", "deep research de Y" ou "levanta isso com fontes
cruzadas". O Claude decide a pasta de destino e roda o workflow.

Também funciona a retomada: "continua a pesquisa sobre X" — ele checa o que já está
salvo em disco antes de gastar qualquer token novo.

Por baixo, o acionamento é:

```
Workflow({
  scriptPath: ".claude/skills/pesquisa-profunda/scripts/deep_research.js",
  args: { pergunta: "<pergunta completa, com contexto/região/formato>",
          pasta: "<onde salvar, ex.: pesquisas/precos-mercado>" }
})
```

## O que sai no fim

Dentro da `pasta` que você indicou:

```
01_escopo.md          → os ângulos de busca escolhidos
02_busca_N.md         → resultados de cada busca
fontes/NN_host.md     → cada fonte puxada, com claims e citações literais
vereditos/NN.md       → o veredito cético de cada claim central
RELATORIO.md          → o produto principal: síntese com achados, confiança e fontes
```

## Quando NÃO usar

Pergunta simples ou fato pontual (um preço, uma data, "isso é verdade?") não precisa
disso — 2-3 buscas web inline resolvem. Este harness é pra quando você quer
profundidade, fontes cruzadas e um relatório que sobrevive à sessão.
