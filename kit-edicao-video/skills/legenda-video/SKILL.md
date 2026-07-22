---
name: legenda-video
description: Queima legenda estilo Reels/Shorts num vídeo, em 6 estilos diferentes (karaokê, palavra gigante, pop, bloco clássico, keyword destacada, minimalista), transcrevendo a fala com IA. Use quando você disser "legenda esse vídeo/reels", "põe legenda estilo reels", "bota legenda queimada", "gera legenda pra esse conteúdo", "legenda com karaokê", "quero a legenda palavra por palavra", ou apontar um vídeo curto de conteúdo pedindo legenda. A legenda sai queimada no vídeo (não é faixa editável no player); edita-se pelo arquivo .ass que fica ao lado. Para legenda de FILME em outro idioma (traduzir), este não é o caminho.
---

# Legenda de vídeo (conteúdo social) — 6 estilos, queimada via ffmpeg

100% ffmpeg. Roda com o venv do `davinci-resolve-mcp` deste repositório.

## Como rodar

```
cd davinci-resolve-mcp
.venv\Scripts\python.exe scripts_resolve\30_legenda_reels.py "C:\caminho\video.mp4" --estilo karaoke
```

Sai `<video> - LEGENDADO.mp4` ao lado. O original não é tocado. Se não houver
transcrição (`<video>.palavras.json`), o script transcreve na hora.

## Estilos (`--estilo`)

`karaoke` (padrão, a palavra falada acende) · `palavra` (uma palavra gigante por
vez) · `pop` (palavra com salto de escala) · `bloco` (2 linhas clássicas na base) ·
`keyword` (palavra-chave destacada) · `minimalista` (fonte fina).

## Editar

- Texto/tempo de uma linha: editar o `<video>.legenda.ass` (texto puro) e rodar de
  novo — o script respeita a edição.
- Trocar de estilo / refazer da fala: `--regerar`.
- Visual geral: dict `ESTILOS` no topo do script.

## Regra de ouro

Legenda é a **última etapa** da edição — é casada com o tempo da fala; cortar depois
desalinha. Ver `kit-edicao-video/COMO_USAR.md`.
