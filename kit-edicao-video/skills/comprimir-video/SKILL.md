---
name: comprimir-video
description: Deixa um vídeo mais leve (comprime o máximo SEM perda visível), converte qualquer formato pra MP4 universal (MOV, MKV, AVI, WMV, WEBM → MP4) e processa PASTA INTEIRA em lote — um "Format Factory" em ffmpeg puro. Use quando você disser "deixa esse vídeo mais leve", "comprime esse vídeo", "reduz o tamanho/peso", "espreme pra caber no WhatsApp/e-mail", "converte esse MOV/MKV pra MP4", "formata esse vídeo", "diminui esse arquivo", ou apontar um vídeo/pasta pesado pedindo pra enxugar. Também quando um vídeo não toca em algum lugar e precisa virar MP4. NÃO é tratamento de áudio isolado (áudio → tratar-audio; cor → colorir-video) nem edição de conteúdo — esta só reduz peso e troca formato, sem mexer no que aparece na tela.
---

# Comprimir vídeo — deixar leve / converter formato (o "Format Factory")

100% ffmpeg. Roda com o venv do `davinci-resolve-mcp` deste repositório.
O original **nunca** é tocado.

## Como rodar

```
cd davinci-resolve-mcp
.venv\Scripts\python.exe scripts_resolve\80_comprimir.py "C:\caminho\video.mov"
```

Sai `<video> - LEVE.mp4` ao lado. Serve pra **um arquivo** ou uma **pasta inteira**
(aponte a pasta → comprime todos os vídeos dela).

## O que ele faz de uma vez

- **Comprime** ao máximo sem perda que o olho vê (CRF).
- **Converte** qualquer formato pra MP4 compatível (H.264 + AAC, `+faststart`, `yuv420p`).
- **Lote**: aponte uma pasta e ele processa todos (`.mov .mkv .avi .wmv .webm .mp4` …).
- Reporta **antes → depois** com o % de redução de cada arquivo.

## Qualidade (`--qualidade`, padrão `maxima`)

| Nível | Cara | Quando |
|---|---|---|
| `maxima` (padrão) | CRF 20, preset slow — **sem perda visível** | uso normal: espremer mantendo qualidade |
| `alta` | CRF 23 — bem menor, perda mínima | quando quer arquivo bem mais leve |
| `leve` | CRF 27 — espreme forte | WhatsApp/e-mail, aceita perder um pouco |

## Bater um peso-alvo (`--alvo-mb`)

Pra limite de tamanho (WhatsApp ~16-25 MB, e-mail): calcula o bitrate pra chegar perto.

```
... 80_comprimir.py "video.mp4" --alvo-mb 25
```

## Codec (`--codec`, padrão `h264`)

- `h264` — toca em tudo (padrão).
- `h265` — ~30% menor ainda, mais lento e menos compatível (bom pra **arquivar**, não pra enviar).

## Nota importante

"Comprimir sem perder **nada**" literal (lossless real) não encolhe o arquivo — deixa
igual ou maior. O que entrega peso menor com qualidade intacta é o CRF baixo do preset
`maxima`. Se um arquivo já vier bem comprimido, o script avisa que ficou igual/maior.

Verificação: `python scripts_resolve\80_comprimir.py --autoteste`.
