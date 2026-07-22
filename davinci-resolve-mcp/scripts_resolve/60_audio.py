"""
ÁUDIO — conserta o som do vídeo: canal L/R, ruído e volume. Fora do Resolve.

Roda no venv do projeto:

  .venv\\Scripts\\python.exe scripts_resolve\\60_audio.py "video.mp4"

Sai "<video> - AUDIO.mp4" ao lado. NÃO reencoda o VÍDEO (copia o stream de
imagem) — só mexe no áudio, então é rápido e sem perda de qualidade de imagem.
O original NÃO é tocado.

O QUE FAZ (tudo ligado por padrão):
  1. Canal:  resolve o som que fica "só de um lado do fone" ou pulando de lado.
             --canais mono (padrão) = soma L+R e joga igual nos dois lados.
                      esq  = usa só o canal esquerdo nos dois lados
                      dir  = usa só o canal direito nos dois lados
                      manter = não mexe nos canais
  2. Ruído:  redução de chiado/ruído de fundo (afftdn) + corte de rumble grave.
             --sem-ruido desliga.
  3. Volume: nivela pro padrão de streaming (loudnorm -16 LUFS).
             --sem-volume desliga.

TESTE (prova a correção de canal medindo os dois lados):
  python 60_audio.py --autoteste
"""

import argparse
import os
import re
import shutil
import subprocess
from glob import glob

# raiz do projeto (um nivel acima de scripts_resolve)
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Ajustes ─────────────────────────────────────────────────────────
RUIDO_NR = 10          # redução de ruído em dB (afftdn); mais alto = mais agressivo
RUMBLE_HZ = 80         # corta abaixo disso (vento/rumble grave)
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"

SUFIXO = " - AUDIO"
LOG = os.path.join(_BASE, "_audio_log.txt")

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


def montar_af(canais, ruido, volume):
    """Monta a cadeia de filtros de áudio na ordem certa."""
    cadeia = []
    if ruido:
        cadeia.append("highpass=f=%d" % RUMBLE_HZ)
        cadeia.append("afftdn=nr=%d" % RUIDO_NR)
    pan = {
        "mono": "pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1",
        "esq":  "pan=stereo|c0=c0|c1=c0",
        "dir":  "pan=stereo|c0=c1|c1=c1",
        "manter": None,
    }.get(canais, "pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1")
    if pan:
        cadeia.append(pan)
    if volume:
        cadeia.append(LOUDNORM)
    return ",".join(cadeia) if cadeia else "anull"


def processar(video, canais, ruido, volume):
    if not os.path.isfile(video):
        raise RuntimeError("Arquivo nao existe: %s" % video)
    ff = achar_ffmpeg()
    af = montar_af(canais, ruido, volume)
    log("Video: %s" % os.path.basename(video))
    log("Filtros de audio: %s" % af)

    base, _ = os.path.splitext(video)
    saida = base + SUFIXO + ".mp4"
    cmd = [
        ff, "-nostdin", "-hide_banner", "-y", "-i", video,
        "-af", af, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", saida,
    ]
    log("ffmpeg tratando o audio (video copiado sem reencode)...")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg falhou:\n%s" % proc.stderr[-800:])
    log("")
    log("PRONTO: %s" % saida)
    log("O video original NAO foi alterado.")
    return saida


# ── Autoteste: mede os dois canais antes/depois ─────────────────────

def _rms_por_canal(arquivo):
    """Retorna [rms_L, rms_R] em dB, via astats do ffmpeg."""
    ff = achar_ffmpeg()
    out = subprocess.run(
        [ff, "-nostdin", "-hide_banner", "-i", arquivo,
         "-af", "astats=metadata=1:reset=0", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    # astats imprime um bloco por canal, com "RMS level dB: <valor>"
    vals = re.findall(r"RMS level dB:\s*(-?[\d.]+|-?inf)", out)
    conv = []
    for v in vals[:2]:
        conv.append(-999.0 if "inf" in v else float(v))
    return conv


def autoteste():
    log("AUTOTESTE — cria audio SÓ no canal esquerdo e checa se vai pros dois")
    ff = achar_ffmpeg()
    tmp = os.path.join(_BASE, "tmp")
    os.makedirs(tmp, exist_ok=True)
    video = os.path.join(tmp, "_autoteste_audio.mp4")
    # video preto + audio estereo com tom SÓ no canal esquerdo (direito mudo)
    r = subprocess.run(
        [ff, "-nostdin", "-hide_banner", "-y",
         "-f", "lavfi", "-i", "color=c=black:s=320x240:d=3",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
         "-filter_complex", "[1:a]pan=stereo|c0=c0|c1=0*c0[a]",
         "-map", "0:v", "-map", "[a]",
         "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", video], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg (teste) falhou:\n%s" % r.stderr[-500:])

    antes = _rms_por_canal(video)
    log("  ANTES  (L, R) dB: %s  <- direito deve estar mudo (-inf/muito baixo)" % antes)

    saida = processar(video, canais="mono", ruido=False, volume=False)
    depois = _rms_por_canal(saida)
    log("  DEPOIS (L, R) dB: %s  <- os dois lados devem ficar parecidos" % depois)

    ok = (len(depois) == 2 and depois[0] > -100 and depois[1] > -100
          and abs(depois[0] - depois[1]) < 1.0)
    log("")
    log("AUTOTESTE %s — correcao de canal %s"
        % ("OK" if ok else "FALHOU", "funcionou" if ok else "NAO bateu"))
    return ok


def main():
    ap = argparse.ArgumentParser(description="Conserta audio: canal L/R, ruido, volume")
    ap.add_argument("video", nargs="?")
    ap.add_argument("--canais", default="mono", choices=["mono", "esq", "dir", "manter"])
    ap.add_argument("--sem-ruido", action="store_true")
    ap.add_argument("--sem-volume", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    args = ap.parse_args()

    log("=" * 62)
    log("AUDIO")
    log("=" * 62)
    try:
        if args.autoteste:
            autoteste()
        elif args.video:
            processar(args.video, args.canais, not args.sem_ruido, not args.sem_volume)
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
