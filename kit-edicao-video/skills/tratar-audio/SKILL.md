---
name: tratar-audio
description: Conserta o áudio de um vídeo — resolve o som que fica "só de um lado do fone" ou pulando de um lado pro outro (canal L/R desbalanceado), reduz ruído/chiado de fundo e nivela o volume. Use quando você disser "arruma o áudio", "o som tá só de um lado", "tá saindo só num fone", "tira o ruído/chiado", "nivela o volume", "conserta o som desse vídeo", ou apontar um vídeo com problema de som. Não reencoda o vídeo (só o áudio) — é rápido e sem perda de imagem. É conserto técnico da captação, não mixagem musical.
---

# Tratar áudio — canal L/R, ruído e volume

100% ffmpeg. **Copia o stream de vídeo sem reencodar** — só o áudio muda.

## Como rodar

```
cd davinci-resolve-mcp
.venv\Scripts\python.exe scripts_resolve\60_audio.py "C:\caminho\video.mp4"
```

Sai `<video> - AUDIO.mp4` ao lado. Por padrão: conserta canal + reduz ruído + nivela.

## O caso do "som só de um lado" (`--canais`)

| Valor | O que faz |
|---|---|
| `mono` (padrão) | soma L+R e joga **igual nos dois lados** — resolve o som que pula de lado ou sai só num fone |
| `esq` | usa só o canal esquerdo nos dois lados |
| `dir` | usa só o canal direito nos dois lados |
| `manter` | não mexe nos canais |

## Ligar/desligar etapas

`--sem-ruido` pula o denoise; `--sem-volume` pula o nivelamento (loudnorm −16 LUFS).
Ajustes finos (`RUIDO_NR`, `RUMBLE_HZ`) no topo do script.
