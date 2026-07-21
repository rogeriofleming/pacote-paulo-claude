# Pacote pro Paulo — organização do Claude Code + Fable Mode + DaVinci MCP

Este repositório reúne seis coisas, cada uma numa pasta:

## 1. `ecossistema-claude/`

Explica a ARQUITETURA de como organizar um "cérebro" no Claude Code — o modelo
de camadas Cérebro → Skills → Agentes → Squads, protocolo de sessão, regras
permanentes, memória vs documento, fonte única. É a estrutura pura, sem
nenhum dado pessoal de quem montou — pra você adaptar com as SUAS preferências
e criar o seu próprio `CLAUDE.md`.

- [`COMO_FUNCIONA.md`](ecossistema-claude/COMO_FUNCIONA.md) — leia primeiro.
- [`CLAUDE_MD_MODELO.md`](ecossistema-claude/CLAUDE_MD_MODELO.md) — template pra preencher.

## 2. `skill-fable-mode/`

Um "modo de operação" pro Claude — um loop de 6 fases (entender → aterrissar
em evidência → planejar → executar com causa-raiz → atacar o próprio trabalho
→ entregar calibrado) que reduz muito erro de LLM tipo afirmar coisa sem
checar ou entregar o primeiro rascunho sem se questionar. Vem em duas formas
(skill e agente) que fazem a mesma coisa por caminhos diferentes.

- [`COMO_USAR.md`](skill-fable-mode/COMO_USAR.md) — leia primeiro, tem o passo a passo de instalação.

## 3. `skill-pesquisa-profunda/`

Um harness de pesquisa multi-fonte com verificação — substitui a skill
`deep-research` oficial do Claude Code, que dispara ~100 subagentes, queima
milhões de tokens e não salva nada em disco (se a sessão morre, perde tudo).
Esta versão tem teto de ~24 agentes, salva cada resultado em disco na hora,
usa um verificador cético por claim e permite retomar de onde parou.

- [`COMO_USAR.md`](skill-pesquisa-profunda/COMO_USAR.md) — leia primeiro, tem instalação e uso.

## 4. `skill-humanizer/`

Tira a "cara de IA" de um texto — deixa a escrita soar natural e humana. Detecta
e conserta 33 padrões típicos de LLM (símbolos inflados, linguagem promocional,
regra de três, excesso de travessão, voz passiva, frases de preenchimento, tom
bajulador). Skill de terceiro (MIT, baseada no guia "Signs of AI writing" da
Wikipedia).

- [`COMO_USAR.md`](skill-humanizer/COMO_USAR.md) — leia primeiro, tem instalação e uso.

## 5. `skill-brevidade-inteligente/`

Reescreve/revisa textos de trabalho (email, mensagem, newsletter, slide, aviso de
equipe) pelo método Brevidade Inteligente da Axios — 1 pessoa, 1 ideia, na frente,
sem enrolação. Combina com o Humanizer: brevidade corta o excesso, humanizer tira a
cara de robô.

- [`COMO_USAR.md`](skill-brevidade-inteligente/COMO_USAR.md) — leia primeiro, tem instalação e uso.

## 6. `davinci-resolve-mcp/`

MCP que conecta o Claude ao DaVinci Resolve, adaptado pra Windows + Resolve
**free** (não exige o Studio pra transcrição local e pros dois scripts de
corte automático — silêncio e vício de linguagem tipo "né"). Fork do projeto
open-source [`barckley75/resolve-claude-mcp`](https://github.com/barckley75/resolve-claude-mcp) (MIT).

- [`INSTRUCOES_PAULO.md`](davinci-resolve-mcp/INSTRUCOES_PAULO.md) — leia primeiro, tem o passo a passo de instalação.
- [`WINDOWS_SETUP.md`](davinci-resolve-mcp/WINDOWS_SETUP.md) — o que foi adaptado/resolvido pra rodar no Windows.
- [`CORTES.md`](davinci-resolve-mcp/CORTES.md) — como usar os dois scripts de corte automático.
