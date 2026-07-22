"""
REFRAME 9:16 — transforma video horizontal em vertical (Reels/Shorts/TikTok).

Roda no venv do projeto (processamento externo, ffmpeg puro — NAO e script de
menu do Resolve, NAO depende do gap AppendToTimeline):

  .venv\\Scripts\\python.exe scripts_resolve\\40_reframe_vertical.py "video.mp4"

Sai "<video> - 9x16.mp4" (1080x1920 por padrao). O original NAO e tocado.

MODOS (--modo):
  blur  (padrao) — video inteiro no centro, sem cortar nada, com o fundo
                   preenchido pelo proprio video borrado. Nao perde imagem.
  crop           — corta as laterais e enche a tela (zoom no meio). Perde as
                   bordas; use --foco esq|centro|dir pra escolher o que fica.
  pad            — barras pretas em cima/baixo (letterbox), imagem inteira.

Trata METADATA DE ROTACAO: se o video ja e vertical (ex.: gravado no celular
em pe), avisa e so normaliza pro preset, sem reenquadrar.

TESTE SEM VIDEO REAL:
  python 40_reframe_vertical.py --autoteste
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from glob import glob

# raiz do projeto (um nivel acima de scripts_resolve)
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Ajustes ─────────────────────────────────────────────────────────
LARG_SAIDA = 1080          # largura do vertical
ALT_SAIDA = 1920           # altura do vertical (1080x1920 = 9:16)
BLUR_SIGMA = 22            # intensidade do desfoque do fundo (modo blur)
CRF = 18                   # qualidade h264 (menor = melhor/maior arquivo)
PRESET_X264 = "medium"
NORMALIZAR_AUDIO = True    # loudnorm (nivela o volume pro padrao de streaming)

SUFIXO = " - 9x16"
LOG = os.path.join(_BASE, "_reframe_vertical_log.txt")

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


# ── ffmpeg / ffprobe ────────────────────────────────────────────────

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


def dimensoes_efetivas(arquivo):
    """(largura, altura) JA considerando a rotacao (display), nao a do sensor.

    Um celular na vertical grava 3840x2160 com rotacao 90/270 -> na tela e
    2160x3840. O ffmpeg auto-rotaciona antes dos filtros, entao precisamos das
    dimensoes efetivas pra decidir se o video e horizontal ou vertical.
    """
    fp = _achar_bin("ffprobe")
    w = h = rot = None
    if fp:
        try:
            out = subprocess.run(
                [fp, "-v", "error", "-select_streams", "v:0",
                 "-show_entries",
                 "stream=width,height:stream_side_data=rotation:stream_tags=rotate",
                 "-of", "default=noprint_wrappers=1", arquivo],
                capture_output=True, text=True).stdout
            mw = re.search(r"width=(\d+)", out)
            mh = re.search(r"height=(\d+)", out)
            mr = re.search(r"rotation=(-?\d+)", out) or re.search(r"rotate=(-?\d+)", out)
            if mw and mh:
                w, h = int(mw.group(1)), int(mh.group(1))
            if mr:
                rot = int(mr.group(1))
        except Exception:
            pass
    if w is None:  # fallback pelo proprio ffmpeg
        out = subprocess.run([achar_ffmpeg(), "-nostdin", "-hide_banner", "-i", arquivo],
                             capture_output=True, text=True).stderr
        m = re.search(r",\s*(\d{2,5})x(\d{2,5})", out)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
        mr = re.search(r"rotate\s*:\s*(-?\d+)", out)
        if mr:
            rot = int(mr.group(1))
    if w is None:
        raise RuntimeError("nao consegui ler a resolucao de '%s'" % arquivo)
    if rot and abs(rot) % 180 == 90:  # 90 ou 270 -> troca w<->h
        w, h = h, w
    return w, h


# ── Filtros de reframe ──────────────────────────────────────────────

def filtro(modo, foco):
    W, H = LARG_SAIDA, ALT_SAIDA
    if modo == "blur":
        # fundo: enche 1080x1920 (corta o excesso) e borra; frente: video
        # inteiro cabendo na largura, centralizado por cima.
        return (
            "[0:v]scale=%d:%d:force_original_aspect_ratio=increase,"
            "crop=%d:%d,gblur=sigma=%d[bg];"
            "[0:v]scale=%d:%d:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1"
            % (W, H, W, H, BLUR_SIGMA, W, H)
        )
    if modo == "pad":
        return (
            "[0:v]scale=%d:%d:force_original_aspect_ratio=decrease,"
            "pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
            % (W, H, W, H)
        )
    if modo == "crop":
        # escala pela altura e corta 1080 de largura no foco escolhido
        x = {"esq": "0", "dir": "iw-%d" % W, "centro": "(iw-%d)/2" % W}.get(foco, "(iw-%d)/2" % W)
        return ("[0:v]scale=-2:%d,crop=%d:%d:%s:0,setsar=1" % (H, W, H, x))
    raise RuntimeError("modo invalido: %s" % modo)


def reencode(video, modo, foco, saida):
    ff = achar_ffmpeg()
    cmd = [
        ff, "-nostdin", "-hide_banner", "-y",
        "-i", video,
        "-filter_complex", filtro(modo, foco),
        "-c:v", "libx264", "-preset", PRESET_X264, "-crf", str(CRF),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
    ]
    if NORMALIZAR_AUDIO:
        cmd += ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]  # alvo de streaming
    cmd += ["-movflags", "+faststart", saida]

    log("ffmpeg reenquadrando (modo=%s)..." % modo)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg falhou:\n%s" % proc.stderr[-800:])
    return saida


# ── Fluxo principal ─────────────────────────────────────────────────

def processar(video, modo, foco):
    if not os.path.isfile(video):
        raise RuntimeError("Arquivo nao existe: %s" % video)
    w, h = dimensoes_efetivas(video)
    log("Video: %s  (efetivo %dx%d)" % (os.path.basename(video), w, h))

    alvo = LARG_SAIDA / float(ALT_SAIDA)   # 0.5625
    atual = w / float(h)
    if atual <= alvo + 0.02:
        log("Este video JA e vertical (>= 9:16) — nao precisa reenquadrar.")
        log("Vou so normalizar pro preset %dx%d (modo pad, sem cortar)." % (LARG_SAIDA, ALT_SAIDA))
        modo = "pad"

    base, _ = os.path.splitext(video)
    saida = base + SUFIXO + ".mp4"
    reencode(video, modo, foco, saida)
    log("")
    log("PRONTO: %s" % saida)
    log("O video original NAO foi alterado.")
    return saida


# ── Autoteste ───────────────────────────────────────────────────────

def autoteste():
    log("AUTOTESTE — gera video horizontal 1920x1080 e reenquadra nos 3 modos")
    ff = achar_ffmpeg()
    tmp = os.path.join(_BASE, "tmp")
    os.makedirs(tmp, exist_ok=True)
    video = os.path.join(tmp, "_autoteste_reframe.mp4")
    # barras coloridas (SMPTE) horizontais + tom, 3s
    cmd = [ff, "-nostdin", "-hide_banner", "-y",
           "-f", "lavfi", "-i", "smptebars=s=1920x1080:d=3",
           "-f", "lavfi", "-i", "sine=frequency=300:duration=3",
           "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-shortest", video]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg (video de teste) falhou:\n%s" % r.stderr[-500:])

    ok_all = True
    for modo in ("blur", "crop", "pad"):
        base, _ = os.path.splitext(video)
        saida = base + "_" + modo + ".mp4"
        reencode(video, modo, "centro", saida)
        w, h = dimensoes_efetivas(saida)
        ok = os.path.isfile(saida) and (w, h) == (LARG_SAIDA, ALT_SAIDA)
        ok_all = ok_all and ok
        log("  modo %-5s -> %dx%d  %s" % (modo, w, h, "OK" if ok else "FALHOU"))
    log("")
    log("AUTOTESTE %s" % ("OK" if ok_all else "FALHOU"))
    return ok_all


def main():
    ap = argparse.ArgumentParser(description="Reenquadra video pra 9:16 vertical (ffmpeg)")
    ap.add_argument("video", nargs="?")
    ap.add_argument("--modo", default="blur", choices=["blur", "crop", "pad"])
    ap.add_argument("--foco", default="centro", choices=["esq", "centro", "dir"],
                    help="qual parte fica no modo crop")
    ap.add_argument("--autoteste", action="store_true")
    args = ap.parse_args()

    log("=" * 62)
    log("REFRAME 9:16")
    log("=" * 62)
    try:
        if args.autoteste:
            autoteste()
        elif args.video:
            processar(args.video, args.modo, args.foco)
        else:
            log("Passe um video, ou use --autoteste.")
    except Exception as e:
        log("ERRO: %s" % e)
        import traceback
        log(traceback.format_exc())
    finally:
        salvar_log()
        log("Log salvo em: %s" % LOG)


if __name__ == "__main__":
    main()
