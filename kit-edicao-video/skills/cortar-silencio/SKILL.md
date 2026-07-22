---
name: cortar-silencio
description: Remove os silêncios/pausas de um vídeo, deixando só os trechos falados, e cospe um MP4 já cortado. Use quando você disser "corta os silêncios", "tira as pausas", "corta os tempos mortos", "deixa só onde eu falo", "jump cut automático", ou apontar um vídeo com muita pausa pedindo pra enxugar. Ideal pra conteúdo de redes sociais (deixa o vídeo dinâmico). Detecta o silêncio pelo volume (ffmpeg), com limiar e folga ajustáveis.
---

# Cortar silêncio — cospe o MP4 cortado

100% ffmpeg. Roda com o venv do `davinci-resolve-mcp` deste repositório.

## Como rodar

```
cd davinci-resolve-mcp
.venv\Scripts\python.exe scripts_resolve\50_cortar_silencio_externo.py "C:\caminho\video.mp4"
```

Sai `<video> - SEM SILENCIO.mp4` ao lado. O original não é tocado. Só ver o que
cortaria, sem gerar: `--so-relatar`.

## Ajustes (no topo do script)

| Constante | Padrão | O que faz |
|---|---|---|
| `SILENCIO_DB` | -34 | abaixo disso é silêncio; ambiente ruidoso → -28 |
| `SILENCIO_MIN` | 0.60s | silêncio mais curto que isso fica no vídeo |
| `FOLGA` | 0.12s | respiro mantido em cada borda do corte |
| `CORTE_MIN` | 0.25s | corte menor que isso não vale o jump cut |

> Há também o `10_cortar_silencio.py` (roda dentro do DaVinci Resolve free, monta
> timeline sem reencodar) — ver `davinci-resolve-mcp/CORTES.md`. Este aqui é o
> externo, que gera o vídeo cortado direto.
