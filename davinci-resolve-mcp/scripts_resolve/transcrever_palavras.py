"""
TRANSCRICAO PALAVRA A PALAVRA — gera o JSON que o 20_cortar_ne.py consome.

Roda no venv do projeto (nao e script de menu do Resolve):
  .venv\\Scripts\\python.exe scripts_resolve\\transcrever_palavras.py "video.mp4"

Saida: "<video>.palavras.json" ao lado do video, com TODAS as palavras e seus
tempos. O corte em si (quais palavras remover) e decisao do script de menu —
assim, mudar a lista de palavras nao exige retranscrever.

Reusa o motor ja validado (WINDOWS_SETUP.md §4): faster-whisper com
decodificacao via ffmpeg CLI + stub do PyAV (Smart App Control).

Modelo: --modelo, senao WHISPER_MODEL, senao "medium" (padrao).
"""

import argparse
import json
import os
import sys

# Este script roda dentro do proprio repositorio (nao e copiado como os
# scripts de menu), entao o caminho e resolvido a partir do proprio arquivo.
COFRE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(COFRE, "src"))

from resolve_claude_mcp.transcription import (  # noqa: E402
    _decode_audio_ffmpeg,
    _fw_model,
    _import_whisper_model,
    DEFAULT_COMPUTE_TYPE,
    DEFAULT_DEVICE,
    SAMPLE_RATE,
)

# Whisper "limpa" vicios de linguagem se deixado solto. Este prompt enviesa
# pra transcricao literal — sem ele, muitos "ne" somem da saida.
PROMPT_LITERAL = (
    "Transcricao literal, palavra por palavra, mantendo vicios de linguagem "
    "e muletas: ne, tipo, entao, ai, ta, ok? Ne? Tipo assim, ne."
)


def transcrever(arquivo, modelo, idioma="pt"):
    WhisperModel = _import_whisper_model()
    audio = _decode_audio_ffmpeg(arquivo)
    duracao = len(audio) / float(SAMPLE_RATE)

    print("Modelo: %s (device=%s, %s) | duracao: %.1fs"
          % (modelo, DEFAULT_DEVICE, DEFAULT_COMPUTE_TYPE, duracao), flush=True)

    wm = WhisperModel(_fw_model(modelo), device=DEFAULT_DEVICE,
                      compute_type=DEFAULT_COMPUTE_TYPE)
    segmentos, info = wm.transcribe(
        audio,
        language=idioma,
        word_timestamps=True,
        vad_filter=True,
        initial_prompt=PROMPT_LITERAL,
    )

    palavras = []
    for seg in segmentos:
        for w in (seg.words or []):
            palavras.append({
                "inicio": round(float(w.start), 3),
                "fim": round(float(w.end), 3),
                "palavra": w.word.strip(),
            })
        print("  ate %6.1fs — %d palavras" % (seg.end, len(palavras)), flush=True)

    return {
        "arquivo": os.path.abspath(arquivo),
        "modelo": modelo,
        "idioma": getattr(info, "language", None) or idioma,
        "duracao": round(duracao, 3),
        "palavras": palavras,
    }


def main():
    ap = argparse.ArgumentParser(description="Transcreve com timestamp por palavra -> JSON")
    ap.add_argument("video")
    ap.add_argument("--modelo", default=os.environ.get("WHISPER_MODEL", "medium"))
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--saida", default=None, help="caminho do JSON (padrao: <video>.palavras.json)")
    args = ap.parse_args()

    if not os.path.isfile(args.video):
        sys.exit("Arquivo nao existe: %s" % args.video)

    dados = transcrever(args.video, args.modelo, args.idioma)

    saida = args.saida or (args.video + ".palavras.json")
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    print("OK: %d palavras -> %s" % (len(dados["palavras"]), saida), flush=True)


if __name__ == "__main__":
    main()
