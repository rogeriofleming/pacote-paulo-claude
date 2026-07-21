# Como instalar e usar o Iniciar Sessão

## O que é

Um protocolo de **abertura de sessão de trabalho**. Faz sempre a mesma rotina disciplinada:
descobre a data/hora reais, sincroniza o git (e integra branches de sessões feitas pelo
celular), lê os documentos de estado do projeto e reporta o estado atual + a próxima ação —
de forma enxuta.

Combina com o **Encerrar Sessão** (neste mesmo repo): um abre, o outro fecha, e juntos
mantêm os documentos de estado sempre confiáveis entre uma sessão e outra.

## Pré-requisito: os documentos de estado

A skill assume que o projeto tem docs de estado — o padrão sugerido:

- `CLAUDE.md` — identidade, papel e regras do projeto (veja a pasta `ecossistema-claude/`
  deste repo pra um template).
- `WORKFLOW.md` — o que está no ar / pendente / em andamento.
- `PROXIMA_SESSAO.md` — o contexto que a sessão anterior deixou.

Se você usa outros nomes, adapte — o método vale igual.

## Instalação

Copie a pasta pra `.claude/skills/iniciar-sessao/` na raiz do seu projeto:
```
.claude/skills/iniciar-sessao/SKILL.md
```

## Como acionar

"inicia a sessão", "começa", ou simplesmente no começo de toda conversa de trabalho.

## Nota sobre o ritual de abertura

O reporte tem um espaço opcional pra um ritual seu (uma intenção, um foco do dia, uma
oração — o que fizer sentido pra você). É pessoal e opcional; use ou remova.
