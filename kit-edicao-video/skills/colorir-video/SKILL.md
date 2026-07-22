---
name: colorir-video
description: Aplica um "look" de cor num vídeo (color grading rápido), em 6 estilos — teal & orange cinematográfico, quente/hora dourada, frio/clean, vibrante pra redes, film fade (contraste baixo com pretos lavados) e preto e branco. Use quando você disser "arruma a cor", "dá um look nesse vídeo", "deixa cinematográfico", "esquenta/esfria a cor", "deixa mais vibrante pra redes", "põe preto e branco", "coloriza", ou apontar um vídeo pedindo tratamento de cor. Tem controle de intensidade (--forca). É grading por preset (rápido, ffmpeg); pra controle fino nó a nó, é no editor de vídeo.
---

# Colorir vídeo — 6 looks de cor

100% ffmpeg. Roda com o venv do `davinci-resolve-mcp` deste repositório.

## Como rodar

```
cd davinci-resolve-mcp
.venv\Scripts\python.exe scripts_resolve\70_cor.py "C:\caminho\video.mp4" --look teal_orange
```

Sai `<video> - COR.mp4` ao lado. O original não é tocado.

## Looks (`--look`)

| Look | Cara |
|---|---|
| `teal_orange` (padrão) | cinema: sombra azul-esverdeada, pele/luz alaranjada |
| `quente` | hora dourada, aconchego |
| `frio` | clean/corporativo (puxa pro azul) |
| `vibrante` | punch de redes (saturação + contraste + nitidez) |
| `film_fade` | cinema moderno: contraste baixo, pretos lavados |
| `pb` | preto e branco contrastado |

## Intensidade

`--forca 0.0..1.5` (1.0 = padrão). Abaixo de 1 mistura com o original (mais sutil);
acima reforça. Cor é gosto: afine pelo `--forca` ou pelo dict `LOOKS` no topo do script.
