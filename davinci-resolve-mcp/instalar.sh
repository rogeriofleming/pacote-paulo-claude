#!/usr/bin/env bash
# Kit de edicao de video - instalador (macOS / Linux)
# Baixa e configura tudo que as skills precisam.
set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "  KIT DE EDICAO DE VIDEO - instalador (macOS/Linux)"
echo "============================================================"

# 1. Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERRO] Python 3.10+ nao encontrado. Instale e rode de novo."
  exit 1
fi
echo "[ok] Python encontrado."

# 2. uv
if ! command -v uv >/dev/null 2>&1; then
  echo "[..] Instalando uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
echo "[ok] uv disponivel."

# 3. ffmpeg (nao instala automatico - gerenciador varia)
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[AVISO] ffmpeg nao encontrado. Instale:"
  echo "        macOS: brew install ffmpeg   |   Debian/Ubuntu: sudo apt install ffmpeg"
  echo "        Depois rode este script de novo."
  exit 1
fi
echo "[ok] ffmpeg encontrado."

# 4. dependencias
echo "[..] Instalando dependencias Python (faster-whisper, etc)..."
uv sync --all-extras
echo "[ok] Dependencias instaladas."

# 5. baixar modelo + testar transcricao
echo "[..] Baixando o modelo Whisper 'medium' (~1,5 GB, so na 1a vez) e testando..."
TMPWAV="$(mktemp).wav"
ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 1 -y "$TMPWAV" >/dev/null 2>&1
if uv run python scripts_resolve/transcrever_palavras.py "$TMPWAV"; then
  echo "[ok] Transcricao funcionando (modelo baixado)."
else
  echo "[AVISO] A transcricao de teste falhou - confira o ffmpeg/whisper."
fi
rm -f "$TMPWAV"

# 6. testar pipeline de video
echo "[..] Testando o pipeline de video (reframe 9:16)..."
uv run python scripts_resolve/40_reframe_vertical.py --autoteste && echo "[ok] Pipeline de video funcionando." || echo "[AVISO] Autoteste de video falhou."

echo "============================================================"
echo "  PRONTO. Leia kit-edicao-video/COMO_USAR.md para usar."
echo "============================================================"
