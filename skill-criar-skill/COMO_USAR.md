# Como instalar e usar o Criar Skill

## O que é

Uma cópia auto-contida e editável da **skill-creator** da Anthropic — a skill que **cria,
refaz e melhora outras skills**. Traz o método rigoroso original (rascunho → casos de
teste → rodar com/sem a skill → avaliar qualitativa e quantitativamente → reescrever até
ficar bom) e acrescenta um **Passo 0 de triagem**: escolhe quanto desse aparato pesado
aplicar conforme o tipo de skill (artefato rico → método completo; efeito objetivo →
verificar o efeito; subjetiva → avaliação qualitativa).

Toda a maquinaria acompanha a pasta: `scripts/` (rodar avaliações, agregar benchmark,
melhorar a description, empacotar), `agents/`, `eval-viewer/`, `references/`, `assets/`.

## Instalação

Copie a **pasta inteira** pra `.claude/skills/criar-skill/` na raiz do seu projeto (o
SKILL.md e todas as subpastas):
```
.claude/skills/criar-skill/SKILL.md
.claude/skills/criar-skill/scripts/...
.claude/skills/criar-skill/agents/...
.claude/skills/criar-skill/eval-viewer/...
.claude/skills/criar-skill/references/...
```

> Os scripts são Python. Rodam com Python 3. Nenhuma configuração pessoal embutida.

## Como acionar

"cria uma skill pra X", "refaz a skill Y", "melhora a skill Z", "otimiza o trigger da
skill W" — mesmo sem dizer "skill-creator".

## Onde começar a ler

O próprio `SKILL.md` — comece pelo **Passo 0 (triagem)** pra decidir o nível de rigor, e
siga pro **Método completo** abaixo (o padrão da Anthropic, preservado). O guia de escrita
de skills e o cuidado com a `description` valem pra qualquer tipo.
