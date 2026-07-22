"""
CORTE DE SILÊNCIO (externo) — cospe o MP4 já cortado, sem abrir o Resolve.

Irmão do 10_cortar_silencio.py, que monta timeline no Resolve. Este aqui é 100%
ffmpeg: detecta os silêncios e MONTA um MP4 novo só com os trechos falados —
ideal pro pipeline automático de conteúdo social.

  .venv\\Scripts\\python.exe scripts_resolve\\50_cortar_silencio_externo.py "video.mp4"

Sai "<video> - SEM SILENCIO.mp4" ao lado. O original NÃO é tocado.

AJUSTES (mesmos do 10_cortar_silencio):
  SILENCIO_DB   abaixo disso é silêncio (-34 p/ voz limpa; -28 se ambiente ruidoso)
  SILENCIO_MIN  silêncio mais curto que isso (s) não é cortado
  FOLGA         respiro mantido em cada borda do corte
  CORTE_MIN     corte menor que isso não vale o jump cut

TESTE (não mexe em nada, só relata):
  python 50_cortar_silencio_externo.py "video.mp4" --so-relatar
"""

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from glob import glob

# raiz do projeto (um nivel acima de scripts_resolve)
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Ajustes ─────────────────────────────────────────────────────────
SILENCIO_DB = -34
SILENCIO_MIN = 0.60
FOLGA = 0.12
CORTE_MIN = 0.25
TRECHO_MIN = 0.20

SUFIXO = " - SEM SILENCIO"
LOG = os.path.join(_BASE, "_corte_silencio_ext_log.txt")

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


# ── Detecção (mesma lógica do 10_cortar_silencio) ───────────────────

def detectar_silencios(arquivo):
    ff = achar_ffmpeg()
    cmd = [ff, "-nostdin", "-hide_banner", "-i", arquivo,
           "-af", "silencedetect=noise=%ddB:d=%s" % (SILENCIO_DB, SILENCIO_MIN),
           "-vn", "-f", "null", "-"]
    saida = subprocess.run(cmd, capture_output=True, text=True).stderr

    duracao = None
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", saida)
    if m:
        duracao = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    if not duracao:
        raise RuntimeError("nao consegui ler a duracao de '%s'" % arquivo)

    silencios, inicio = [], None
    for linha in saida.splitlines():
        m = re.search(r"silence_start:\s*(-?[\d.]+)", linha)
        if m:
            inicio = max(0.0, float(m.group(1)))
            continue
        m = re.search(r"silence_end:\s*(-?[\d.]+)", linha)
        if m and inicio is not None:
            silencios.append((inicio, float(m.group(1))))
            inicio = None
    if inicio is not None:
        silencios.append((inicio, duracao))
    return silencios, duracao


def calcular_trechos(silencios, duracao):
    trechos, cursor = [], 0.0
    for ini, fim in silencios:
        if ini > cursor:
            trechos.append([cursor, ini])
        cursor = max(cursor, fim)
    if cursor < duracao:
        trechos.append([cursor, duracao])
    trechos = [[max(0.0, i - FOLGA), min(duracao, f + FOLGA)] for i, f in trechos]
    fundidos = []
    for i, f in trechos:
        if fundidos and i - fundidos[-1][1] < CORTE_MIN:
            fundidos[-1][1] = max(fundidos[-1][1], f)
        else:
            fundidos.append([i, f])
    return [(i, f) for i, f in fundidos if f - i >= TRECHO_MIN]


def fmt(seg):
    m, s = divmod(seg, 60)
    return "%02d:%06.3f" % (int(m), s)


# ── Corte + concatenação via ffmpeg ─────────────────────────────────

def montar_mp4(video, trechos, saida):
    """Monta o MP4 final só com os trechos, via trim+concat (filtergraph)."""
    ff = achar_ffmpeg()
    partes = []
    labels = []
    for n, (ini, fim) in enumerate(trechos):
        partes.append("[0:v]trim=start=%.3f:end=%.3f,setpts=PTS-STARTPTS[v%d];"
                      % (ini, fim, n))
        partes.append("[0:a]atrim=start=%.3f:end=%.3f,asetpts=PTS-STARTPTS[a%d];"
                      % (ini, fim, n))
        labels.append("[v%d][a%d]" % (n, n))
    fg = "".join(partes) + "".join(labels) + \
        "concat=n=%d:v=1:a=1[v][a]" % len(trechos)

    # filtergraph pode ficar grande -> passa por arquivo (limite de comando no Windows)
    fd, script = tempfile.mkstemp(suffix=".txt", text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(fg)
    try:
        cmd = [ff, "-nostdin", "-hide_banner", "-y", "-i", video,
               "-filter_complex_script", script,
               "-map", "[v]", "-map", "[a]",
               "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
               "-movflags", "+faststart", saida]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError("ffmpeg falhou:\n%s" % proc.stderr[-800:])
    finally:
        try:
            os.remove(script)
        except Exception:
            pass
    return saida


def processar(video, so_relatar=False):
    if not os.path.isfile(video):
        raise RuntimeError("Arquivo nao existe: %s" % video)
    log("Analisando: %s" % os.path.basename(video))
    log("  (limiar %d dB, silencio min %.2fs, folga %.2fs)"
        % (SILENCIO_DB, SILENCIO_MIN, FOLGA))
    silencios, duracao = detectar_silencios(video)
    trechos = calcular_trechos(silencios, duracao)
    mantido = sum(f - i for i, f in trechos)

    log("Duracao: %s | silencios: %d | trechos de fala: %d"
        % (fmt(duracao), len(silencios), len(trechos)))
    log("Mantido: %s (%.0f%%) | removido: %s"
        % (fmt(mantido), 100.0 * mantido / duracao if duracao else 0, fmt(duracao - mantido)))

    if not trechos:
        log("Nada a montar: nenhum trecho de fala sobrou. Confira SILENCIO_DB.")
        return None
    if so_relatar:
        for n, (i, f) in enumerate(trechos, 1):
            log("  %3d. %s -> %s  (%.2fs)" % (n, fmt(i), fmt(f), f - i))
        return None

    base, _ = os.path.splitext(video)
    saida = base + SUFIXO + ".mp4"
    log("")
    log("Montando o MP4 cortado (%d trechos)..." % len(trechos))
    montar_mp4(video, trechos, saida)
    log("")
    log("PRONTO: %s" % saida)
    log("O video original NAO foi alterado.")
    return saida


def autoteste():
    log("AUTOTESTE — video com fala/silencio/fala; confere que a saida encurtou")
    ff = achar_ffmpeg()
    tmp = os.path.join(_BASE, "tmp")
    os.makedirs(tmp, exist_ok=True)
    video = os.path.join(tmp, "_autoteste_silencio.mp4")
    # 6s: som 0-2, SILENCIO 2-4, som 4-6
    r = subprocess.run(
        [ff, "-nostdin", "-hide_banner", "-y",
         "-f", "lavfi", "-i", "color=c=black:s=320x240:d=6",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
         "-filter_complex", "[1:a]volume=enable='between(t,2,4)':volume=0[a]",
         "-map", "0:v", "-map", "[a]",
         "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", video], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg (teste) falhou:\n%s" % r.stderr[-500:])

    saida = processar(video)
    if not saida:
        log("AUTOTESTE FALHOU — nao gerou saida")
        return False
    # mede a duração da saída
    out = subprocess.run([ff, "-nostdin", "-hide_banner", "-i", saida],
                         capture_output=True, text=True).stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", out)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0
    ok = 3.5 < dur < 5.5   # ~4s de fala + 2 folgas, bem menos que os 6 originais
    log("")
    log("Duracao final: %.2fs (original 6.0s)" % dur)
    log("AUTOTESTE %s" % ("OK" if ok else "FALHOU"))
    return ok


def main():
    ap = argparse.ArgumentParser(description="Corta silencios e cospe o MP4 (ffmpeg)")
    ap.add_argument("video", nargs="?")
    ap.add_argument("--so-relatar", action="store_true", help="so mostra os cortes")
    ap.add_argument("--autoteste", action="store_true")
    args = ap.parse_args()

    log("=" * 62)
    log("CORTE DE SILENCIO (externo)")
    log("=" * 62)
    try:
        if args.autoteste:
            autoteste()
        elif args.video:
            processar(args.video, so_relatar=args.so_relatar)
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
