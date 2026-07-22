"""
COR — aplica um "look" de cor no vídeo, 100% fora do Resolve (ffmpeg puro).

Roda no venv do projeto:

  .venv\\Scripts\\python.exe scripts_resolve\\70_cor.py "video.mp4" --look teal_orange

Sai "<video> - COR.mp4" ao lado. O original NÃO é tocado.

LOOKS (--look, ou --listar):
  teal_orange  cinematográfico: sombra azul-esverdeada, pele/luz alaranjada
  quente       hora dourada, aconchego (puxa pro âmbar)
  frio         clean/corporativo (puxa pro azul, leve dessaturação)
  vibrante     punch de redes sociais (saturação + contraste altos)
  film_fade    cinema moderno: contraste baixo, pretos lavados
  pb           preto e branco contrastado

Os looks vivem no dict LOOKS (cadeias de filtro ffmpeg) — dá pra afinar cada um
ou criar um novo. INTENSIDADE global: --forca 0.0..1.5 (1.0 = como definido).

TESTE: python 70_cor.py --autoteste
"""

import argparse
import os
import shutil
import subprocess
from glob import glob

# raiz do projeto (um nivel acima de scripts_resolve)
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Looks (cadeias de filtro ffmpeg) ────────────────────────────────
# Mantidos moderados de propósito — cor é gosto, e o --forca ajusta a dose.
LOOKS = {
    "teal_orange": (
        "colorbalance=rs=-0.08:bs=0.10:rm=0.06:bm=-0.04:rh=0.10:bh=-0.10,"
        "eq=contrast=1.08:saturation=1.10"
    ),
    "quente": (
        "colortemperature=temperature=4800,"
        "eq=saturation=1.10:contrast=1.05:brightness=0.02"
    ),
    "frio": (
        "colortemperature=temperature=8200,"
        "eq=saturation=0.97:contrast=1.06"
    ),
    "vibrante": (
        "eq=saturation=1.35:contrast=1.12:brightness=0.02,"
        "unsharp=5:5:0.5"
    ),
    "film_fade": (
        "curves=all='0/0.06 0.5/0.5 1/0.95',"
        "eq=saturation=0.90:contrast=0.95"
    ),
    "pb": (
        "eq=saturation=0.0:contrast=1.18:brightness=0.01"
    ),
}

SUFIXO = " - COR"
LOG = os.path.join(_BASE, "_cor_log.txt")

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


def _achar_bin(nome):
    env = os.environ.get(nome.upper() + "_BINARY")
    if env and os.path.isfile(env):
        return env
    achado = shutil.which(nome)
    if achado:
        return achado
    local = os.environ.get("LOCALAPPDATA")
    if local:
        hits = glob(os.path.join(local, "Microsoft", "WinGet", "Packages",
                                 "Gyan.FFmpeg*", "**", "bin", nome + ".exe"),
                    recursive=True)
        if hits:
            return hits[0]
    return None


def achar_ffmpeg():
    b = _achar_bin("ffmpeg")
    if not b:
        raise RuntimeError("ffmpeg nao encontrado. Instale com: winget install Gyan.FFmpeg")
    return b


def filtro_com_forca(look, forca):
    """Mistura o look com o original via 'blend' quando forca != 1.

    forca=1 -> look cheio. 0 -> quase sem efeito. >1 -> exagera (via eq extra).
    Implementado com um overlay/blend simples: aplica o look num ramo e mistura
    com o original por opacidade = min(1, forca). Acima de 1, reforça saturação.
    """
    base = LOOKS[look]
    if abs(forca - 1.0) < 0.01:
        return "[0:v]%s,setsar=1[v]" % base
    op = max(0.0, min(1.0, forca))
    reforco = ""
    if forca > 1.0:
        reforco = ",eq=saturation=%.2f:contrast=%.2f" % (1 + (forca - 1) * 0.4,
                                                         1 + (forca - 1) * 0.15)
    return (
        "[0:v]split=2[a][b];"
        "[b]%s%s[look];"
        "[a][look]blend=all_mode=normal:all_opacity=%.2f,setsar=1[v]"
        % (base, reforco, op)
    )


def aplicar(video, look, forca, saida):
    ff = achar_ffmpeg()
    fc = filtro_com_forca(look, forca)
    cmd = [
        ff, "-nostdin", "-hide_banner", "-y", "-i", video,
        "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-movflags", "+faststart", saida,
    ]
    log("ffmpeg aplicando o look '%s' (forca %.2f)..." % (look, forca))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg falhou:\n%s" % proc.stderr[-800:])
    return saida


def processar(video, look, forca):
    if not os.path.isfile(video):
        raise RuntimeError("Arquivo nao existe: %s" % video)
    if look not in LOOKS:
        raise RuntimeError("Look '%s' nao existe. Opcoes: %s" % (look, ", ".join(LOOKS)))
    log("Video: %s | look: %s | forca: %.2f" % (os.path.basename(video), look, forca))
    base, _ = os.path.splitext(video)
    saida = base + SUFIXO + ".mp4"
    aplicar(video, look, forca, saida)
    log("")
    log("PRONTO: %s" % saida)
    log("O video original NAO foi alterado.")
    return saida


def autoteste():
    log("AUTOTESTE — aplica os %d looks num video sintetico" % len(LOOKS))
    ff = achar_ffmpeg()
    tmp = os.path.join(_BASE, "tmp")
    os.makedirs(tmp, exist_ok=True)
    video = os.path.join(tmp, "_autoteste_cor.mp4")
    r = subprocess.run(
        [ff, "-nostdin", "-hide_banner", "-y",
         "-f", "lavfi", "-i", "testsrc2=s=1280x720:d=2",
         "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", video],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg (video de teste) falhou:\n%s" % r.stderr[-500:])
    ok_all = True
    for look in LOOKS:
        saida = os.path.splitext(video)[0] + "_" + look + ".mp4"
        aplicar(video, look, 1.0, saida)
        ok = os.path.isfile(saida) and os.path.getsize(saida) > 5000
        ok_all = ok_all and ok
        log("  look %-12s -> %s" % (look, "OK" if ok else "FALHOU"))
    log("")
    log("AUTOTESTE %s" % ("OK" if ok_all else "FALHOU"))
    return ok_all


def main():
    ap = argparse.ArgumentParser(description="Aplica look de cor no video (ffmpeg)")
    ap.add_argument("video", nargs="?")
    ap.add_argument("--look", default="teal_orange")
    ap.add_argument("--forca", type=float, default=1.0, help="0.0..1.5 (1.0 = padrao)")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    args = ap.parse_args()

    if args.listar:
        for nome in LOOKS:
            print("  %s" % nome)
        return

    log("=" * 62)
    log("COR (%s)" % args.look)
    log("=" * 62)
    try:
        if args.autoteste:
            autoteste()
        elif args.video:
            processar(args.video, args.look, args.forca)
        else:
            log("Passe um video, ou use --autoteste. Looks: %s" % ", ".join(LOOKS))
    except Exception as e:
        log("ERRO: %s" % e)
        import traceback
        log(traceback.format_exc())
    finally:
        salvar_log()
        log("Log salvo em: %s" % LOG)


if __name__ == "__main__":
    main()
