# Como organizar um "cérebro" no Claude Code

> Este documento explica a ARQUITETURA — o esquema de organização — de um jeito de trabalhar com o Claude Code que funciona bem na prática. Não tem nenhum dado pessoal de quem montou: é a estrutura pura, pra você adaptar com as SUAS preferências, projetos e regras.

---

## A ideia central: 4 camadas, cada uma com um papel diferente

```
Cérebro (CLAUDE.md)  →  Skills (funcionário)  →  Agentes (gerente autônomo)  →  Squads (time)
```

| Camada | O que é | Quando usar |
|---|---|---|
| **Cérebro** | O `CLAUDE.md` na raiz do projeto — identidade, regras, protocolos. É lido no início de toda sessão. | Sempre — é o "sistema operacional" da conversa. |
| **Skill** | Um arquivo `SKILL.md` com um processo documentado pra UMA tarefa recorrente. | Tarefa que se repete e tem um jeito certo de ser feita. |
| **Agente** | Um "personagem" com system prompt próprio, chamado via `Task`/`Agent` tool, que roda sozinho e devolve resultado. | Tarefa que vale a pena delegar/paralelizar, ou que pede um modo de operação diferente do principal (ex.: revisor cético). |
| **Squad** | Múltiplos agentes especializados coordenados pra um fluxo de várias etapas. | Fluxo complexo com etapas claramente separáveis (ex.: pesquisa → rascunho → revisão → design). |

A regra prática: **comece simples**. A maioria das necessidades vira Skill. Só sobe pra Agente quando faz sentido rodar em paralelo ou isolado do contexto principal. Squad é raro — só quando o fluxo tem etapas de verdade distintas.

---

## 1. O CLAUDE.md — a espinha dorsal

Fica na raiz do repositório (ou em `~/.claude/CLAUDE.md` pra regras globais de todas as sessões). É lido automaticamente todo início de sessão. As seções que valem a pena ter:

1. **Identidade e papel** — quem o Claude é neste projeto, o que ele NÃO deve fazer.
2. **Postura** — como falar com você: direto? formal? quanto de contexto explicar?
3. **Mapa de quando-é-aqui vs quando-é-em-outro-projeto** — se você tem múltiplos projetos, uma tabela simples evita o Claude tentar fazer tudo no lugar errado.
4. **Protocolo de início de sessão** — passos fixos pra toda sessão nova (ex.: ler tal arquivo, checar tal status).
5. **Protocolo de encerramento** — o que fica registrado ao fim de uma sessão de trabalho (ver seção 4).
6. **Regras operacionais permanentes** — ver seção 3, é a parte que mais compensa manter viva.
7. **Travas de segurança explícitas** — qualquer ação de alto risco (mexer em dinheiro, publicar coisa pública, deletar) merece uma regra em maiúsculo, no topo, com o motivo.

**Princípio geral:** o CLAUDE.md deve ficar ENXUTO. Detalhe pesado de um projeto específico vai pra um arquivo próprio daquele projeto, e o CLAUDE.md aponta pra lá — não duplica.

---

## 2. Multi-projeto: um cérebro coordenador + projetos-satélite

Se você tem mais de uma área de trabalho (ex.: um projeto de código, um de conteúdo, um pessoal), um padrão que funciona bem:

- Um projeto "cérebro" — onde você pensa, decide, organiza, cria skills/agentes novos, e mantém o contexto sobre VOCÊ (preferências, padrões, pessoas envolvidas).
- Projetos-satélite — cada um com o contexto PESADO da área dele (documentos, histórico, arquivos de trabalho). A execução pesada acontece lá, não no cérebro.
- Um arquivo `MAPA_PROJETOS.md` no cérebro lista o que cada satélite faz, pra você (e o Claude) saber pra onde ir.

Isso evita duas dores: (a) o cérebro inchar com detalhe de todo projeto, (b) cada projeto satélite duplicar as mesmas regras de postura/segurança — essas ficam UMA vez no cérebro.

---

## 3. "Regras operacionais permanentes" — o mecanismo que mais compensa

Toda vez que você corrige o Claude de forma não-óbvia ("não faz assim, faz assado"), isso vira uma REGRA NUMERADA e PERMANENTE, guardada num documento lido toda sessão — não só na memória da conversa (que se perde).

Formato que funciona:

```
N. **Nome curto da regra** — a regra em 1-2 frases.
   Motivo/caso que gerou a regra (opcional, mas ajuda a julgar exceções).
```

Prática: manter um "resumo" curto (uma linha por regra, lido sempre) e um arquivo "detalhado" separado (o caso completo por trás de cada regra, lido só quando surge dúvida de aplicação). Isso evita que o contexto de toda sessão fique pesado com histórico que só importa em caso de dúvida.

**Por que isso importa mais do que parece:** um LLM sem esse mecanismo comete o MESMO erro de novo em sessões diferentes, porque a correção ficou presa numa conversa que já foi. Transformar correção em regra documentada é o que faz o sistema "aprender" de verdade.

---

## 4. Memória do Claude Code × Documentos — a distinção que evita dado velho

O Claude Code tem um sistema de memória automática (arquivos que persistem entre conversas). É tentador usar pra tudo. **Não use pra tudo.**

- **Memória** → serve só pra o Claude se lembrar de COMO agir (preferências de estilo, o que evitar, contexto de projeto em andamento). Você raramente vai abrir esses arquivos.
- **Documento versionado** (no seu repositório, em Markdown) → qualquer coisa que você mesmo vai querer abrir e achar depois: status de um projeto, uma decisão, um número, uma instrução durável.

Regra de bolso: **"eu vou querer abrir isso sozinho depois?"** Se sim, é documento, não memória. Memória que vira "lar" de uma informação importante é a receita pra você perguntar "cadê aquilo" e o Claude não achar (porque memória é consultada sob demanda, não é garantida entrar no contexto).

---

## 5. Fonte única — cada informação mora em UM lugar

Se um dado (status de uma tarefa, um número, uma decisão) existe em mais de um documento, um dia os dois vão dessincronizar e o Claude vai afirmar o dado velho como se fosse atual. Prática:

1. Antes de gravar um dado novo, checar se ele já existe em outro lugar (buscar no repositório).
2. Se já existe, escolher o "dono" e nos outros lugares deixar só um ponteiro ("ver X").
3. Quando um dado muda, atualizar SÓ a fonte única — e, se houver cópias legadas espalhadas, corrigir todas na hora.

---

## 6. Protocolo de início/fim de sessão

Ter um roteiro FIXO (não uma lembrança solta) pro início e pro fim de cada sessão de trabalho evita perda de contexto entre sessões. Pode virar uma Skill própria (ex.: `iniciar-sessao`, `encerrar-sessao`).

**Início — passos típicos:**
1. Confirmar data/hora reais (LLMs erram isso sozinhos).
2. Sincronizar o repositório (se trabalha de mais de uma máquina).
3. Ler CLAUDE.md + o resumo de regras + o que ficou pendente da sessão anterior.
4. Classificar o pedido: é conversa/decisão (fica no cérebro) ou é execução (vai pro projeto certo)?

**Encerramento — passos típicos:**
1. Registrar o que foi decidido/aprendido em DOCUMENTO (não memória) — a "colheita" da sessão.
2. Verificar fonte única — nenhum dado duplicado ficou desatualizado.
3. Atualizar o status do projeto (arquivo de status/roadmap).
4. Deixar um "próxima sessão" — o que fica pendente, pra não começar do zero.
5. Limpar arquivos temporários.
6. Sincronizar (commit/push) o repositório.

---

## 7. Skills — anatomia de um funcionário

Uma skill é uma pasta com um `SKILL.md`:

```yaml
---
name: nome-da-skill
description: Descrição de UMA frase que diz O QUE ela faz e QUANDO usar — inclui as palavras/gatilhos que o usuário costuma dizer. Isso é o que o Claude lê pra decidir se aciona a skill sozinho.
---

# Corpo da skill: o processo passo a passo, decisões, formato de saída.
```

Boas práticas:
- A `description` é o gatilho — escreva pensando em "que frases a pessoa vai usar pra pedir isso".
- Referências grandes (tabelas de dados, exemplos extensos) vão numa subpasta `references/`, citada dentro do SKILL.md — só carrega se for preciso, economiza contexto.
- Uma skill nova nasce, na prática, de um processo que você já faz "na mão" mais de uma vez — documentar o processo é a skill.

## 8. Agentes — anatomia de um gerente autônomo

Um agente é um arquivo (ex.: `.claude/agents/nome.md`) com `name` + `description` (o gatilho) e um corpo que é o SYSTEM PROMPT dele — como ele deve pensar, que regras seguir, que tom usar. É chamado via `Task`/`Agent` tool e roda com contexto próprio (não polui a conversa principal).

Quando vale a pena: tarefa que se beneficia de rodar ISOLADA (ex.: um revisor que não deve ver o raciocínio de quem escreveu, pra não herdar o viés) ou tarefas paralelizáveis.

## 9. Squads — quando o fluxo tem etapas de verdade

Um squad é um conjunto de agentes especializados + um "orquestrador" que decide a ordem. Só compensa quando o trabalho tem estágios claramente separáveis (ex.: pesquisar → escrever → revisar → montar visual), cada um bem servido por um agente com foco estreito.

---

## Resumo de uma frase por camada

- **CLAUDE.md**: quem eu sou e como me comportar nesta casa.
- **Skill**: como fazer ESTA tarefa específica, sempre do mesmo jeito bom.
- **Agente**: um modo de pensar diferente, isolado, chamável sob demanda.
- **Squad**: vários agentes, um fluxo, uma entrega.

Adapte tudo isso com as SUAS regras, seus projetos e sua forma de trabalhar — a estrutura é o que importa, o conteúdo é seu.
