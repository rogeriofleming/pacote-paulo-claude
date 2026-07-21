"""
Local audio transcription.

Two backends, picked automatically:
  - macOS / Apple Silicon  -> mlx-whisper (runs on the Neural Engine/GPU)
  - Windows / Linux         -> faster-whisper (CTranslate2; CPU or CUDA)

For the mlx backend, long files are split into chunks with ffmpeg so each
transcription call completes well within any MCP timeout. faster-whisper
streams segments from a generator and decodes media on its own (via PyAV),
so it handles long files natively without the ffmpeg step.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import types
from typing import Optional, List, Dict, Any

logger = logging.getLogger("ResolveMCP")

# ── Models ──────────────────────────────────────────────────────────

# mlx-whisper HuggingFace repos (macOS backend)
WHISPER_MODELS = {
    "tiny": "mlx-community/whisper-tiny",
    "base": "mlx-community/whisper-base",
    "small": "mlx-community/whisper-small",
    "medium": "mlx-community/whisper-medium",
    "large": "mlx-community/whisper-large-v3",
    "turbo": "mlx-community/whisper-large-v3-turbo",
}

# faster-whisper model sizes (Windows/Linux backend). The same friendly names
# map to CTranslate2 model identifiers that faster-whisper downloads on demand.
FW_MODELS = {
    "tiny": "tiny",
    "base": "base",
    "small": "small",
    "medium": "medium",
    "large": "large-v3",
    "turbo": "large-v3",  # reliable across versions; pass "large-v3-turbo" explicitly if supported
}

# Override per machine with WHISPER_MODEL (see .mcp.json). "turbo" suits the mlx
# backend on Apple silicon; on a CPU-only Windows box "medium" is the measured
# sweet spot — see WINDOWS_SETUP.md §4 for the benchmark.
DEFAULT_MODEL = os.environ.get("WHISPER_MODEL", "turbo")

# Each chunk is this many seconds — short enough to never time out (mlx path)
CHUNK_SECONDS = 300  # 5 minutes


def _get_model_repo(model: str) -> str:
    if "/" in model:
        return model
    repo = WHISPER_MODELS.get(model)
    if repo is None:
        raise ValueError(
            f"Unknown model '{model}'. Choose from: {', '.join(WHISPER_MODELS.keys())} "
            f"or pass a full HuggingFace repo path."
        )
    return repo


def _fw_model(model: str) -> str:
    """Resolve a friendly model name to a faster-whisper model id (else pass through)."""
    return FW_MODELS.get(model, model)


def _select_backend() -> str:
    """Return 'mlx' if mlx-whisper is importable (macOS), otherwise 'faster'."""
    if sys.platform.startswith("darwin"):
        try:
            import mlx_whisper  # noqa: F401
            return "mlx"
        except ImportError:
            pass
    return "faster"


# ── ffmpeg helpers (mlx path only) ──────────────────────────────────

def _get_duration(path: str) -> float:
    """Get duration in seconds via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        path,
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return float(out)


def _extract_chunk(src: str, start: float, duration: float, dst: str):
    """Extract a chunk of audio with ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-t", str(duration),
        "-i", src,
        "-vn",                # drop video
        "-acodec", "pcm_s16le",
        "-ar", "16000",       # whisper expects 16 kHz
        "-ac", "1",           # mono
        dst,
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def _split_audio(path: str, chunk_sec: int, tmp_dir: str) -> List[Dict[str, Any]]:
    """Split into ≤chunk_sec WAV files.  Returns list of {path, offset}."""
    total = _get_duration(path)
    chunks = []
    offset = 0.0
    idx = 0
    while offset < total:
        chunk_path = os.path.join(tmp_dir, f"chunk_{idx:04d}.wav")
        _extract_chunk(path, offset, chunk_sec, chunk_path)
        chunks.append({"path": chunk_path, "offset": offset})
        offset += chunk_sec
        idx += 1
    return chunks


# ── Core transcription (dispatcher) ─────────────────────────────────

def transcribe(
    audio_path: str,
    model: str = DEFAULT_MODEL,
    language: Optional[str] = None,
    word_timestamps: bool = False,
    initial_prompt: Optional[str] = None,
    chunk_seconds: int = CHUNK_SECONDS,
) -> Dict[str, Any]:
    """
    Transcribe an audio/video file locally, choosing the right backend for the OS.

    Returns a dict: {"language": str, "text": str, "segments": [{start, end, text}, ...]}
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # No explicit prompt? Use the saved glossary so proper nouns come out right
    # without anyone having to remember to pass them.
    if initial_prompt is None:
        initial_prompt = load_glossary_prompt()
        if initial_prompt:
            logger.info("Using glossary as initial_prompt (%d chars)", len(initial_prompt))

    backend = _select_backend()
    if backend == "mlx":
        result = _transcribe_mlx(
            audio_path, model, language, word_timestamps, initial_prompt, chunk_seconds
        )
    else:
        result = _transcribe_faster(
            audio_path, model, language, word_timestamps, initial_prompt
        )

    # Second layer: fix whatever the prompt didn't.
    rules = load_corrections()
    if rules:
        for seg in result.get("segments", []):
            seg["text"] = apply_corrections(seg["text"], rules)
        if result.get("text"):
            result["text"] = apply_corrections(result["text"], rules)
        logger.info("Applied %d correction rule(s)", len(rules))

    return result


# ── faster-whisper backend (Windows / Linux) ────────────────────────

SAMPLE_RATE = 16000  # what Whisper expects

# CPU is the reliable default: CTranslate2's CUDA path needs cuBLAS/cuDNN shipped
# separately (nvidia-cublas-cu12, nvidia-cudnn-cu12), and "auto" picks CUDA the
# moment it sees an NVIDIA card — then dies at encode time if those are missing.
# Override with WHISPER_DEVICE=cuda / WHISPER_COMPUTE_TYPE=int8_float16.
DEFAULT_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
DEFAULT_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")


def _find_ffmpeg() -> Optional[str]:
    """Locate an ffmpeg executable: env var, PATH, then a winget install."""
    from glob import glob

    env = os.environ.get("FFMPEG_BINARY")
    if env and os.path.isfile(env):
        return env

    found = shutil.which("ffmpeg")
    if found:
        return found

    # winget (Gyan.FFmpeg) drops it here; PATH only updates on a new shell.
    local = os.environ.get("LOCALAPPDATA")
    if local:
        pattern = os.path.join(
            local, "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "**", "bin", "ffmpeg.exe"
        )
        hits = glob(pattern, recursive=True)
        if hits:
            return hits[0]
    return None


def _decode_audio_ffmpeg(path: str, sample_rate: int = SAMPLE_RATE):
    """Decode any media file to a mono float32 numpy array via the ffmpeg CLI.

    faster-whisper normally decodes with PyAV, but PyAV ships unsigned FFmpeg
    DLLs that Windows Smart App Control blocks. Handing transcribe() a ready
    numpy array skips PyAV's decode path entirely.
    """
    import numpy as np

    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg not found. Install it with:  winget install Gyan.FFmpeg\n"
            "Or set the FFMPEG_BINARY environment variable to its full path."
        )

    cmd = [
        ffmpeg, "-nostdin", "-threads", "0",
        "-i", path,
        "-f", "s16le",          # raw 16-bit PCM to stdout
        "-ac", "1",             # mono
        "-acodec", "pcm_s16le",
        "-ar", str(sample_rate),
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace")[-500:]
        raise RuntimeError(f"ffmpeg failed to decode '{path}':\n{err}")
    if not proc.stdout:
        raise RuntimeError(f"ffmpeg produced no audio from '{path}' — does it have an audio track?")

    return np.frombuffer(proc.stdout, np.int16).astype(np.float32) / 32768.0


def _import_whisper_model():
    """Import faster-whisper's WhisperModel, stubbing PyAV if its DLLs are blocked.

    PyAV is only used by faster-whisper to decode media. We decode with ffmpeg and
    pass a numpy array, so the stub just needs to satisfy the module-level
    `import av` in faster_whisper/audio.py.
    """
    try:
        import av  # noqa: F401
    except ImportError as e:
        if "DLL load failed" not in str(e):
            raise
        logger.info("PyAV unavailable (%s) — stubbing it; decoding via ffmpeg instead.", e)
        stub = types.ModuleType("av")
        stub.__getattr__ = lambda name: (_ for _ in ()).throw(  # type: ignore[attr-defined]
            RuntimeError("PyAV is stubbed out; audio is decoded with the ffmpeg CLI.")
        )
        sys.modules.setdefault("av", stub)

    try:
        from faster_whisper import WhisperModel
        return WhisperModel
    except ImportError as e:
        raise ImportError(
            f"faster-whisper is not importable: {e}\n"
            "Install with: uv pip install 'faster-whisper>=1.0.0'"
        ) from e


def _transcribe_faster(
    audio_path: str,
    model: str,
    language: Optional[str],
    word_timestamps: bool,
    initial_prompt: Optional[str],
) -> Dict[str, Any]:
    WhisperModel = _import_whisper_model()

    size = _fw_model(model)
    logger.info("Transcribing '%s' with faster-whisper (%s)", audio_path, size)

    audio = _decode_audio_ffmpeg(audio_path)

    logger.info("Whisper device=%s compute_type=%s", DEFAULT_DEVICE, DEFAULT_COMPUTE_TYPE)
    wm = WhisperModel(size, device=DEFAULT_DEVICE, compute_type=DEFAULT_COMPUTE_TYPE)

    segments_gen, info = wm.transcribe(
        audio,
        language=language,
        initial_prompt=initial_prompt,
        word_timestamps=word_timestamps,
        vad_filter=True,
    )

    all_segments: List[Dict[str, Any]] = []
    text_parts: List[str] = []
    for seg in segments_gen:
        all_segments.append({
            "start": float(seg.start),
            "end": float(seg.end),
            "text": seg.text,
        })
        if seg.text:
            text_parts.append(seg.text.strip())

    return {
        "language": getattr(info, "language", None) or "unknown",
        "text": " ".join(text_parts),
        "segments": all_segments,
    }


# ── mlx-whisper backend (macOS / Apple Silicon) ─────────────────────

def _transcribe_mlx(
    audio_path: str,
    model: str,
    language: Optional[str],
    word_timestamps: bool,
    initial_prompt: Optional[str],
    chunk_seconds: int,
) -> Dict[str, Any]:
    try:
        import mlx_whisper
    except ImportError:
        raise ImportError(
            "mlx-whisper is not installed. Install with: "
            "uv pip install 'mlx-whisper>=0.4.3'"
        )

    repo = _get_model_repo(model)
    duration = _get_duration(audio_path)

    decode_options: Dict[str, Any] = {}
    if language:
        decode_options["language"] = language

    # Short file → transcribe directly
    if duration <= chunk_seconds:
        logger.info("Transcribing '%s' (%.0fs) with %s", audio_path, duration, repo)
        return mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=repo,
            word_timestamps=word_timestamps,
            initial_prompt=initial_prompt,
            verbose=False,
            **decode_options,
        )

    # Long file → chunk, transcribe each, stitch
    logger.info(
        "Splitting '%s' (%.0fs) into %d-second chunks",
        audio_path, duration, chunk_seconds,
    )
    tmp_dir = tempfile.mkdtemp(prefix="resolve_whisper_")
    try:
        chunks = _split_audio(audio_path, chunk_seconds, tmp_dir)
        logger.info("Created %d chunks", len(chunks))

        all_segments: List[Dict[str, Any]] = []
        all_text_parts: List[str] = []
        detected_language = None

        for i, chunk in enumerate(chunks):
            logger.info("Transcribing chunk %d/%d (offset %.0fs)...", i + 1, len(chunks), chunk["offset"])

            result = mlx_whisper.transcribe(
                chunk["path"],
                path_or_hf_repo=repo,
                word_timestamps=word_timestamps,
                initial_prompt=initial_prompt,
                verbose=False,
                **decode_options,
            )

            if detected_language is None:
                detected_language = result.get("language")

            offset = chunk["offset"]
            for seg in result.get("segments", []):
                all_segments.append({
                    "start": seg["start"] + offset,
                    "end": seg["end"] + offset,
                    "text": seg["text"],
                })

            text = result.get("text", "")
            if text:
                all_text_parts.append(text.strip())

            # Use the tail of the last chunk's text as prompt for the next
            # to maintain context continuity across chunk boundaries
            if text:
                initial_prompt = text.strip()[-200:]

        return {
            "language": detected_language or "unknown",
            "text": " ".join(all_text_parts),
            "segments": all_segments,
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ── Vocabulary: glossary prompt + post-correction map ──────────────
#
# Whisper mangles proper nouns it has never seen ("arcanjo Miguel" -> "a canjo-miguel").
# Two layers fix that, and both live in editable files so a fix stays fixed:
#   nomes.txt      -> fed to the model as initial_prompt (biases decoding upfront)
#   correcoes.txt  -> deterministic search/replace afterwards (catches the rest)

def _vocab_dir() -> str:
    """Where the vocabulary files live. Override with WHISPER_VOCAB_DIR."""
    env = os.environ.get("WHISPER_VOCAB_DIR")
    if env:
        return env
    # <repo>/vocabulario — this file is at <repo>/src/resolve_claude_mcp/
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "vocabulario")
    )


def _read_vocab_lines(filename: str) -> List[str]:
    """Read a vocab file, dropping blanks and # comments. Missing file = []."""
    path = os.path.join(_vocab_dir(), filename)
    if not os.path.isfile(path):
        logger.debug("Vocab file not found: %s", path)
        return []
    lines = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines


def load_glossary_prompt() -> Optional[str]:
    """Build an initial_prompt from nomes.txt, or None if empty.

    Whisper reads only ~224 tokens of prompt and keeps the TAIL when it overflows,
    so file order matters: later entries survive truncation.
    """
    names = _read_vocab_lines("nomes.txt")
    if not names:
        return None
    return ", ".join(names) + "."


def load_corrections() -> List[tuple]:
    """Parse correcoes.txt into [(wrong, right), ...], in file order."""
    rules = []
    for line in _read_vocab_lines("correcoes.txt"):
        if "=>" not in line:
            logger.warning("Ignoring malformed correction (no '=>'): %r", line)
            continue
        wrong, right = line.split("=>", 1)
        wrong, right = wrong.strip(), right.strip()
        if wrong:
            rules.append((wrong, right))
    return rules


def apply_corrections(text: str, rules: Optional[List[tuple]] = None) -> str:
    """Apply the correction map to a string, case-insensitively, on word boundaries."""
    import re

    if rules is None:
        rules = load_corrections()
    for wrong, right in rules:
        # \b fails next to non-word chars (e.g. a trailing "-"), so only use it
        # where the edge is actually a word char.
        left = r"\b" if wrong[:1].isalnum() else ""
        right_b = r"\b" if wrong[-1:].isalnum() else ""
        pattern = left + re.escape(wrong) + right_b
        text = re.sub(pattern, right.replace("\\", r"\\"), text, flags=re.IGNORECASE)
    return text


def apply_corrections_to_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run the correction map over every segment's text (loads rules once)."""
    rules = load_corrections()
    if not rules:
        return segments
    for seg in segments:
        seg["text"] = apply_corrections(seg["text"], rules)
    return segments


# ── SRT helpers ────────────────────────────────────────────────────

def segments_to_srt(segments: List[Dict[str, Any]]) -> str:
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _seconds_to_srt_time(seg["start"])
        end = _seconds_to_srt_time(seg["end"])
        text = seg["text"].strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


def _seconds_to_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
