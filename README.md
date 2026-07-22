# Pacote pro Paulo — organização do Claude Code, skills e DaVinci MCP

Este repositório reúne doze coisas, cada uma numa pasta:

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

## 6. `skill-find-skills/`

Ajuda a **descobrir e instalar skills** do ecossistema aberto (o "app store" de skills
via `npx skills` / skills.sh) — busca por assunto, filtra por qualidade e mostra o
comando de instalar. Quase toda genérica (é da Anthropic); com uma nota de segurança
antes de instalar coisa de terceiro.

- [`COMO_USAR.md`](skill-find-skills/COMO_USAR.md) — leia primeiro.

## 7. `skill-criar-skill/`

Cópia editável da **skill-creator** da Anthropic — a skill que **cria, refaz e melhora
outras skills**. Método rigoroso completo (rascunho → testes → avaliar → reescrever) +
um Passo 0 de triagem que adapta o nível de rigor ao tipo de skill. Vem com toda a
maquinaria (scripts Python, agentes, eval-viewer).

- [`COMO_USAR.md`](skill-criar-skill/COMO_USAR.md) — leia primeiro.

## 8. `skill-iniciar-sessao/`

Protocolo de **abertura de sessão**: descobre data/hora, sincroniza o git (e integra
branches de sessão do celular), lê os docs de estado do projeto e reporta o estado +
próxima ação. Par do encerrar-sessao.

- [`COMO_USAR.md`](skill-iniciar-sessao/COMO_USAR.md) — leia primeiro.

## 9. `skill-encerrar-sessao/`

Protocolo de **fechamento de sessão** — encerrar não é faxina, é **colheita**: relê a
conversa e roteia cada aprendizado pro lugar único e certo (feedback→memória,
conhecimento→doc, método novo→skill), mantém fonte única, atualiza os docs de estado e
sincroniza. Par do iniciar-sessao.

- [`COMO_USAR.md`](skill-encerrar-sessao/COMO_USAR.md) — leia primeiro.

## 10. `Apometria/`

Base de conhecimento **geral e público** sobre Apometria, montada no modelo de estudos
do Obsidian (uma pasta-assunto com notas atômicas conectadas por `[[links]]`). Pra
estudar e pra treinar o Claude no assunto. Só conhecimento geral — sem material
proprietário de nenhum terapeuta.

- [`Apometria.md`](Apometria/Apometria.md) — nota-índice, comece por ela.
- [`README.md`](Apometria/README.md) — como a pasta foi montada.

## 11. `davinci-resolve-mcp/`

MCP que conecta o Claude ao DaVinci Resolve, adaptado pra Windows + Resolve
**free** (não exige o Studio pra transcrição local e pros dois scripts de
corte automático — silêncio e vício de linguagem tipo "né"). Fork do projeto
open-source [`barckley75/resolve-claude-mcp`](https://github.com/barckley75/resolve-claude-mcp) (MIT).

- [`INSTRUCOES_PAULO.md`](davinci-resolve-mcp/INSTRUCOES_PAULO.md) — leia primeiro, tem o passo a passo de instalação.
- [`WINDOWS_SETUP.md`](davinci-resolve-mcp/WINDOWS_SETUP.md) — o que foi adaptado/resolvido pra rodar no Windows.
- [`CORTES.md`](davinci-resolve-mcp/CORTES.md) — como usar os dois scripts de corte automático.

## 12. `skill-responsivar-mobile/`

Pega um **arquivo HTML** e o deixa **responsivo perfeito no celular** (telas 5", 5.5" e
6"+), mexendo **só em CSS** dentro de `@media (max-width)` — sem tocar no layout desktop e
sem reestruturar o HTML. Não faz "no olho": roda um **loop verificado num browser real**
que mede o overflow horizontal em 5 larguras e **aponta o elemento que está vazando a
tela**, até fechar em zero. Inclui o motor de medição e um exemplo quebrado pra testar.

- [`COMO_USAR.md`](skill-responsivar-mobile/COMO_USAR.md) — leia primeiro, tem instalação e uso.

## 13. `kit-edicao-video/`

Kit pra **editar vídeo de conteúdo** (Reels/Shorts/TikTok) **sem o DaVinci Resolve** —
é tudo **ffmpeg puro**. Automatiza a parte chata: **legenda** queimada em 6 estilos
(karaokê, palavra gigante, pop, bloco, keyword, minimalista), **cor** em 6 looks
(teal&orange, quente, frio, vibrante, film fade, p&b), **áudio** (conserta o som que
sai "só de um lado", tira ruído, nivela volume), **corte de silêncio** e **reframe
9:16**. Inclui 4 skills mecânicas + um **estrategista de retenção** (`reels-estrategista`:
analisa o vídeo, decide COMO editar pra prender com base em ciência de atenção, e só
então orquestra as mecânicas — a cabeça, não só a mão) + um **agente** que edita de
ponta a ponta na ordem certa. Roda junto do `davinci-resolve-mcp` (mesmo venv e transcrição).

- **Instalação num clique:** `davinci-resolve-mcp/INSTALAR.bat` (Windows) ou `instalar.sh` (mac/Linux) baixa e configura tudo (uv, ffmpeg, faster-whisper, modelo Whisper) e testa. **Abrindo este repo no Claude Code, ele já te oferece rodar isso** — é só confirmar.
- [`COMO_USAR.md`](kit-edicao-video/COMO_USAR.md) — leia primeiro.
- [`referencias/GUIA_RETENCAO.md`](kit-edicao-video/referencias/GUIA_RETENCAO.md) — os princípios de retenção (ciência × prática × ofício) que o estrategista usa pra decidir.
- [`conhecimento-edicao/`](kit-edicao-video/conhecimento-edicao/) — o corpo de conhecimento de pesquisa por trás do kit: automação do DaVinci por Python (free × Studio), boas práticas de edição + bancos de recursos 100% grátis (licença conferida), e o que editores profissionais reais dizem sobre o ofício.
- Scripts em [`davinci-resolve-mcp/scripts_resolve/`](davinci-resolve-mcp/scripts_resolve/) (`30`–`70`).
