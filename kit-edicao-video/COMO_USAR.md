# Kit de Edição de Vídeo — leia primeiro

Um conjunto de ferramentas pra editar vídeo de conteúdo (Reels/Shorts/TikTok)
**sem precisar do DaVinci Resolve** — é tudo **ffmpeg puro** (Python chamando o
ffmpeg). Serve pra automatizar a parte chata da edição: legenda, cor, áudio, corte
de silêncio e reenquadramento pra vertical.

Feito pra rodar junto do `davinci-resolve-mcp` deste mesmo repositório: os scripts
ficam em **`davinci-resolve-mcp/scripts_resolve/`** e usam o mesmo `.venv` e o mesmo
motor de transcrição (faster-whisper) que já vêm configurados lá.

## Instalar (jeito fácil)

Na pasta `davinci-resolve-mcp`, dê duplo clique em **`INSTALAR.bat`** (Windows) ou
rode **`./instalar.sh`** (macOS/Linux): ele instala tudo (uv, ffmpeg, faster-whisper),
baixa o modelo Whisper e testa. Detalhe em `davinci-resolve-mcp/INSTRUCOES_PAULO.md`.
Os pré-requisitos abaixo são o que o instalador cuida por você.

## Pré-requisitos

1. Ter o `davinci-resolve-mcp` instalado (ver `davinci-resolve-mcp/INSTRUCOES_PAULO.md`)
   — é ele que traz o `.venv`, o ffmpeg e a transcrição local.
2. `ffmpeg` no PATH (`winget install Gyan.FFmpeg` no Windows).

Tudo aqui roda com o Python do venv do `davinci-resolve-mcp`:
```
cd davinci-resolve-mcp
.venv\Scripts\python.exe scripts_resolve\<script>.py "C:\caminho\video.mp4"
```

## As 5 ferramentas → scripts (em `davinci-resolve-mcp/scripts_resolve/`)

| Ferramenta | Script | O que faz | Saída |
|---|---|---|---|
| Áudio | `60_audio.py` | conserta canal L/R (som "de um lado só"), ruído, volume | `- AUDIO.mp4` |
| Cor | `70_cor.py --look <>` | 6 looks (teal_orange, quente, frio, vibrante, film_fade, pb) | `- COR.mp4` |
| Cortar silêncio | `50_cortar_silencio_externo.py` | remove pausas, cospe o MP4 cortado | `- SEM SILENCIO.mp4` |
| Reframe 9:16 | `40_reframe_vertical.py --modo <>` | horizontal → vertical (blur/crop/pad) | `- 9x16.mp4` |
| Legenda | `30_legenda_reels.py --estilo <>` | 6 estilos de legenda queimada | `- LEGENDADO.mp4` |

> Nenhum script toca o arquivo original — sempre gera um novo ao lado.
> Cada um tem `--autoteste` (roda num vídeo sintético pra provar que funciona) e um
> cabeçalho no topo explicando os ajustes.

## A ordem certa (é lei)

```
áudio  →  cor  →  cortar silêncio  →  reframe 9:16  →  legenda
```

A **legenda é sempre a última**, porque ela é casada com o tempo exato da fala — se
você cortar ou acelerar o vídeo depois de legendar, tudo desalinha. Cor e áudio
podem vir primeiro (não mexem no tempo). Cada etapa consome a saída da anterior.

## Estilos de legenda (`--estilo`)

`karaoke` (a palavra falada acende) · `palavra` (uma palavra gigante por vez) ·
`pop` (palavra com salto de escala) · `bloco` (2 linhas clássicas) · `keyword`
(palavra-chave destacada) · `minimalista` (fonte fina).

A legenda sai **queimada** no vídeo. Pra ajustar, edite o arquivo `.ass` que fica ao
lado do vídeo (texto puro) e rode de novo — o script respeita a edição. Trocar de
estilo depois de editar: `--regerar`.

## Looks de cor (`--look`)

`teal_orange` (cinema) · `quente` · `frio` · `vibrante` (redes) · `film_fade`
(pretos lavados) · `pb`. Intensidade: `--forca 0.0..1.5`. Cor é gosto — se ficar
forte/fraco, ajuste o `--forca` ou o dict `LOOKS` no topo do script.

## As skills, o estrategista e o agente

Nesta pasta tem, no formato do Claude Code:
- `skills/` — 5 skills que você pode instalar no seu Claude Code pra acionar por
  linguagem natural:
  - **4 mecânicas** (`legenda-video`, `colorir-video`, `tratar-audio`,
    `cortar-silencio`) — cada uma executa uma ferramenta.
  - **`reels-estrategista`** — a **cabeça** que decide COMO editar pra prender: ela
    analisa o vídeo, diagnostica retenção (hook, ritmo, onde cortar), monta um
    **Plano de Retenção** pra você aprovar e só então orquestra as mecânicas na
    ordem certa. Use quando a decisão de o que fazer ainda não foi tomada ("edita
    esse reels pra prender", "me diz onde cortar"). As mecânicas continuam pra
    quando você já sabe o que quer (só legenda, só cor).
- `referencias/GUIA_RETENCAO.md` — os **princípios de retenção** (hook, variação,
  ritmo, cortes) com o peso de evidência de cada um (ciência dura × prática de
  mercado × ofício de editor). É o que o estrategista consulta pra decidir.
- `conhecimento-edicao/` — o **corpo de conhecimento** por trás do kit (pesquisa com
  fontes): `automacao-davinci-python.md` (o que dá pra automatizar no Resolve free ×
  Studio, via Python), `boas-praticas-e-recursos-gratis.md` (o que faz um vídeo
  prender + bancos de música/b-roll/fontes/templates 100% grátis, licença conferida) e
  `o-que-editores-reais-dizem.md` (editores profissionais nomeados sobre o ofício).
- `agente/editor-video.md` — um **agente** que edita um vídeo de ponta a ponta,
  orquestrando as ferramentas na ordem certa. Aciona com "edita esse vídeo".

Ajuste os caminhos dentro das skills/agente pro lugar onde você clonou o repo.
