# Como instalar e usar o Fable Mode

## O que é

Um "modo de operação" — não troca o modelo, muda a DISCIPLINA com que ele trabalha. É um loop de 6 fases (entender → aterrissar em evidência → planejar → executar com causa-raiz → atacar o próprio trabalho → entregar calibrado) que reduz muito o tipo de erro mais comum de LLM: afirmar coisa que não checou, "confirmar" reexecutando o mesmo raciocínio, ou entregar o primeiro rascunho sem se questionar.

Existe em duas formas, que fazem a mesma coisa por caminhos diferentes:

- **Skill** (`SKILL.md`) — o Claude principal lê e segue o processo na própria conversa.
- **Agente** (`agente-fable-mode.md`) — você delega a tarefa pra um subagente que roda isolado (não vê seu raciocínio, não herda seu viés) e devolve o resultado já verificado.

## Instalação

1. Copie `SKILL.md` e a pasta `references/` para `.claude/skills/fable-mode/` na raiz do seu projeto:
   ```
   .claude/skills/fable-mode/SKILL.md
   .claude/skills/fable-mode/references/harness_multiagente.md
   ```
2. Copie `agente-fable-mode.md` para `.claude/agents/fable-mode.md`:
   ```
   .claude/agents/fable-mode.md
   ```
3. Nenhum dos dois precisa de configuração adicional — o Claude Code carrega skills e agentes automaticamente a partir dessas pastas.

## Como acionar

**Como skill** (na conversa principal): diga "modo fable", "nível fable", "faz teu melhor nisso", "qualidade máxima". O Claude também deve acionar sozinho em entregas de risco (código pra produção, análise que decide algo, números que vão ser usados) — isso está descrito na `description` do SKILL.md, que é o gatilho automático.

**Como agente** (delegando pra rodar isolado): "manda pro fable", "roda isso no agente fable", ou peça diretamente para usar a tool `Agent`/`Task` com o agente `fable-mode`.

## Quando NÃO vale a pena

Conversa trivial, pergunta rápida, tarefa mecânica de um passo só. O modo gasta mais tempo e tool calls de propósito — é pra quando o custo de estar errado é maior que o custo de checar.

## O arquivo de referência (harness multiagente)

`references/harness_multiagente.md` é o "modo pesado" — só entra em jogo em tarefas grandes (auditoria ampla, pesquisa profunda, revisão extensa de código) quando você tem subagentes disponíveis. Descreve 5 padrões (verificação adversarial, lentes diversas, painel de juízes, loop-até-secar, crítico de completude) — todos derivam do mesmo princípio: quem verifica não pode ser quem fez.
