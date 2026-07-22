"""
COMPRIMIR — deixa o vídeo mais leve (um "Format Factory"), 100% ffmpeg.

Comprime ao máximo SEM perda visível, converte qualquer formato pra MP4
universal, e roda em LOTE (pasta inteira). Roda no venv do projeto:

  .venv\\Scripts\\python.exe scripts_resolve\\80_comprimir.py "video.mov"
  .venv\\Scripts\\python.exe scripts_resolve\\80_comprimir.py "C:\\pasta_de_videos"  (lote)

Sai "<video> - LEVE.mp4" ao lado. O original NUNCA é tocado.

QUALIDADE (--qualidade, padrão = maxima):
  maxima   CRF 20 · preset slow  — comprime o máximo SEM perda que o olho vê
  alta     CRF 23 · preset slow  — arquivo bem menor, perda mínima
  leve     CRF 27 · preset medium— espremer forte pra WhatsApp/e-mail (perde um pouco)

Por PESO-ALVO (--alvo-mb 25): calcula o bitrate pra bater ~25 MB (bom pra limite
de WhatsApp/e-mail). Ignora --qualidade quando usado.

CODEC (--codec, padrão h264):
  h264   máxima compatibilidade (toca em tudo)
  h265   ~30% menor ainda, mais lento, menos compatível (bom pra arquivar)

TESTE: python 80_comprimir.py --autoteste
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from glob import glob

# raiz do projeto (um nivel acima de scripts_resolve)
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Presets de qualidade (CRF = qualidade x tamanho; menor CRF = melhor/maior) ──
PRESETS = {
    "maxima": {"crf": 20, "preset": "slow"},    # sem perda visível — padrão
    "alta":   {"crf": 23, "preset": "slow"},
    "leve":   {"crf": 27, "preset": "medium"},
}

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".wmv", ".flv", ".webm",
             ".m4v", ".mpg", ".mpeg", ".ts", ".3gp")

SUFIXO = " - LEVE"
LOG = os.path.join(_BASE, "_comprimir_log.txt")

_linhas = []


def log(txt=""):
    txt = str(txt)
    _linhas.append(txt)
    try:
        print(txt, flush=True)
    except Exception:
        print(txt.encode("ascii", "replace").decode(), flush=True)


def salvar_log():
    try:
        with open(LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(_linhas))
    except Exception:
        pass


def achar_bin(nome):
    """ffmpeg/ffprobe do PATH; cai pro build do winget se preciso."""
    p = shutil.which(nome)
    if p:
        return p
    base = os.path.expanduser(
        r"~\AppData\Local\Microsoft\WinGet\Packages"
        r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    )
    for hit in glob(os.path.join(base, "**", nome + ".exe"), recursive=True):
        return hit
    return nome  # deixa o subprocess falhar com mensagem clara


FFMPEG = achar_bin("ffmpeg")
FFPROBE = achar_bin("ffprobe")


def mb(caminho):
    try:
        return os.path.getsize(caminho) / (1024 * 1024)
    except OSError:
        return 0.0


def duracao_seg(caminho):
    """Duração em segundos via ffprobe (0 se falhar)."""
    try:
        out = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "json", caminho],
            capture_output=True, text=True,
        )
        return float(json.loads(out.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def tem_audio(caminho):
    try:
        out = subprocess.run(
            [FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries",
             "stream=index", "-of", "csv=p=0", caminho],
            capture_output=True, text=True,
        )
        return bool(out.stdout.strip())
    except Exception:
        return True


def saida_para(entrada):
    base, _ = os.path.splitext(entrada)
    return base + SUFIXO + ".mp4"


def comprimir_um(entrada, qualidade, codec, alvo_mb):
    if not os.path.isfile(entrada):
        log(f"  ✗ não achei: {entrada}")
        return False

    saida = saida_para(entrada)
    vcodec = "libx265" if codec == "h265" else "libx264"
    orig_mb = mb(entrada)

    cmd = [FFMPEG, "-y", "-i", entrada, "-map", "0:v:0", "-c:v", vcodec]

    if alvo_mb:
        # bitrate de vídeo pra bater ~alvo_mb (reserva ~10% pro áudio/overhead)
        dur = duracao_seg(entrada)
        if dur <= 0:
            log("  ✗ não consegui medir a duração pra calcular o peso-alvo.")
            return False
        audio_kbps = 128
        total_kbps = (alvo_mb * 8192) / dur          # MB→kbit / s
        v_kbps = max(200, int(total_kbps - audio_kbps))
        cmd += ["-b:v", f"{v_kbps}k", "-preset", "slow"]
        modo = f"alvo ~{alvo_mb} MB ({v_kbps}k vídeo)"
    else:
        pr = PRESETS[qualidade]
        cmd += ["-crf", str(pr["crf"]), "-preset", pr["preset"]]
        modo = f"{qualidade} (CRF {pr['crf']}, {pr['preset']})"

    # compatibilidade universal + streaming
    cmd += ["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    if codec == "h265":
        cmd += ["-tag:v", "hvc1"]                     # pra tocar em Apple

    if tem_audio(entrada):
        cmd += ["-map", "0:a:0?", "-c:a", "aac", "-b:a", "128k"]
    else:
        cmd += ["-an"]

    cmd.append(saida)

    log(f"  {os.path.basename(entrada)}  [{modo}, {codec}]  {orig_mb:.1f} MB → ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log("  ✗ ffmpeg falhou:")
        log("    " + (r.stderr or "").strip().splitlines()[-1:][0] if r.stderr else "")
        return False

    novo_mb = mb(saida)
    if novo_mb <= 0:
        log("  ✗ saída vazia.")
        return False
    reducao = (1 - novo_mb / orig_mb) * 100 if orig_mb else 0
    seta = "↓" if novo_mb < orig_mb else "↑"
    log(f"  ✓ {orig_mb:.1f} MB → {novo_mb:.1f} MB  ({seta}{abs(reducao):.0f}%)  →  "
        f"{os.path.basename(saida)}")
    if novo_mb >= orig_mb:
        log("    ⚠ ficou igual/maior — o original já estava bem comprimido; "
            "tente --qualidade leve ou --alvo-mb.")
    return True


def coletar(entrada):
    """Arquivo → [arquivo]; pasta → todos os vídeos dela (sem os já-LEVE)."""
    if os.path.isdir(entrada):
        achados = []
        for nome in sorted(os.listdir(entrada)):
            cam = os.path.join(entrada, nome)
            if (os.path.isfile(cam)
                    and os.path.splitext(nome)[1].lower() in VIDEO_EXTS
                    and SUFIXO not in nome):
                achados.append(cam)
        return achados
    return [entrada]


def autoteste():
    """Gera um clipe sintético, comprime e confere que a saída existe e roda."""
    log("AUTOTESTE — gerando clipe de 3s e comprimindo…")
    tmp = os.path.join(_BASE, "_teste_comprimir.mp4")
    gen = subprocess.run(
        [FFMPEG, "-y", "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30:duration=3",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
         "-c:v", "libx264", "-crf", "12", "-c:a", "aac", "-pix_fmt", "yuv420p", tmp],
        capture_output=True, text=True,
    )
    if gen.returncode != 0 or not os.path.isfile(tmp):
        log("✗ não consegui gerar o clipe de teste (ffmpeg no PATH?).")
        return 1
    ok = comprimir_um(tmp, "maxima", "h264", None)
    saida = saida_para(tmp)
    passou = ok and os.path.isfile(saida) and mb(saida) > 0
    for f in (tmp, saida):
        try:
            os.remove(f)
        except OSError:
            pass
    log("✓ AUTOTESTE PASSOU" if passou else "✗ AUTOTESTE FALHOU")
    return 0 if passou else 1


def main():
    ap = argparse.ArgumentParser(description="Comprime/converte vídeo (leve), ffmpeg puro.")
    ap.add_argument("entrada", nargs="?", help="arquivo de vídeo OU pasta (lote)")
    ap.add_argument("--qualidade", choices=list(PRESETS), default="maxima")
    ap.add_argument("--codec", choices=["h264", "h265"], default="h264")
    ap.add_argument("--alvo-mb", type=float, default=None,
                    help="peso final desejado em MB (ex.: 25 pro WhatsApp)")
    ap.add_argument("--autoteste", action="store_true")
    args = ap.parse_args()

    if args.autoteste:
        code = autoteste()
        salvar_log()
        sys.exit(code)

    if not args.entrada:
        ap.error("informe um arquivo ou pasta de vídeo.")

    itens = coletar(args.entrada)
    if not itens:
        log("Nenhum vídeo encontrado.")
        salvar_log()
        sys.exit(1)

    log(f"COMPRIMIR — {len(itens)} arquivo(s)")
    ok = 0
    for it in itens:
        if comprimir_um(it, args.qualidade, args.codec, args.alvo_mb):
            ok += 1
    log(f"\nPronto: {ok}/{len(itens)} comprimido(s).")
    salvar_log()
    sys.exit(0 if ok == len(itens) else 1)


if __name__ == "__main__":
    main()
