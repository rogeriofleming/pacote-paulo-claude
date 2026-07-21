"""
CORTE DE SILENCIO — monta uma timeline nova sem os trechos mudos.

Funciona no Resolve FREE porque roda POR DENTRO (menu Workspace > Scripts),
nao por conexao externa. A tecnica: o ffmpeg detecta os silencios no arquivo
de midia, e o script monta uma timeline nova ("<clipe> - SEM SILENCIO") usando
AppendToTimeline com subclipes — so os trechos com fala entram.

O ORIGINAL NAO E TOCADO: nem o arquivo, nem a timeline existente.

COMO USAR:
  1. Instale com instalar_scripts.bat (ou copie este arquivo para
     %APPDATA%\\Blackmagic Design\\DaVinci Resolve\\Support\\Fusion\\Scripts\\Utility\\)
  2. No Resolve, selecione o clipe no Media Pool (ou deixe ele como primeiro
     clipe da timeline atual)
  3. Menu Workspace > Scripts > 10_cortar_silencio
  4. A timeline nova aparece no Media Pool ja aberta

AJUSTES (edite as constantes abaixo):
  SILENCIO_DB   — abaixo deste volume e silencio. -34 serve pra gravacao de
                  voz com pouco ruido; ambiente barulhento -> tente -28.
  SILENCIO_MIN  — silencio mais curto que isso (segundos) nao e cortado.
  FOLGA         — respiro mantido em cada borda do corte (evita corte seco).
  CORTE_MIN     — se depois da folga o corte ficar menor que isso, nem corta
                  (evita metralhadora de jump cuts).

TESTE SEM RESOLVE (mostra o que seria cortado, nao mexe em nada):
  python 10_cortar_silencio.py "D:\\caminho\\video.mp4"

⚠️ Este arquivo e uma COPIA quando instalado — o original vive no repositorio
clonado, em scripts_resolve/. Edite o original e reinstale.

⚠️ EDITE LOG abaixo pro caminho onde VOCE clonou este repositorio — o script
roda copiado pra outra pasta do Resolve, entao nao da pra descobrir o caminho
do repositorio sozinho.
"""

import os
import re
import subprocess
import sys

# ── Ajustes ─────────────────────────────────────────────────────────
SILENCIO_DB = -34      # dB; abaixo disso = silencio
SILENCIO_MIN = 0.60    # s; silencio mais curto que isso fica
FOLGA = 0.12           # s; respiro mantido em cada borda
CORTE_MIN = 0.25       # s; corte menor que isso nao vale o jump cut
TRECHO_MIN = 0.20      # s; trecho de fala menor que isso e descartado

SUFIXO_TIMELINE = " - SEM SILENCIO"
LOG = r"C:\CAMINHO\PARA\davinci-resolve-mcp\_corte_silencio_log.txt"

_linhas = []


def log(txt=""):
    txt = str(txt)
    _linhas.append(txt)
    try:
        print(txt)
    except Exception:
        print(txt.encode("ascii", "replace").decode())


def salvar_log():
    try:
        with open(LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(_linhas))
    except Exception:
        pass


# ── ffmpeg ──────────────────────────────────────────────────────────

def achar_ffmpeg():
    """ffmpeg: env FFMPEG_BINARY, PATH, ou a instalacao do winget (Gyan.FFmpeg)."""
    import shutil
    from glob import glob

    env = os.environ.get("FFMPEG_BINARY")
    if env and os.path.isfile(env):
        return env
    achado = shutil.which("ffmpeg")
    if achado:
        return achado
    local = os.environ.get("LOCALAPPDATA")
    if local:
        hits = glob(os.path.join(local, "Microsoft", "WinGet", "Packages",
                                 "Gyan.FFmpeg*", "**", "bin", "ffmpeg.exe"),
                    recursive=True)
        if hits:
            return hits[0]
    return None


def detectar_silencios(arquivo):
    """Roda o silencedetect do ffmpeg. Retorna (lista [(ini, fim)], duracao)."""
    ffmpeg = achar_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("ffmpeg nao encontrado. Instale com: winget install Gyan.FFmpeg")

    cmd = [
        ffmpeg, "-nostdin", "-hide_banner",
        "-i", arquivo,
        "-af", "silencedetect=noise=%ddB:d=%s" % (SILENCIO_DB, SILENCIO_MIN),
        "-vn", "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True)
    saida = proc.stderr.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg falhou lendo '%s':\n%s" % (arquivo, saida[-500:]))

    duracao = None
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", saida)
    if m:
        duracao = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    if not duracao:
        raise RuntimeError("nao consegui ler a duracao de '%s'" % arquivo)

    silencios = []
    inicio = None
    for linha in saida.splitlines():
        m = re.search(r"silence_start:\s*(-?[\d.]+)", linha)
        if m:
            inicio = max(0.0, float(m.group(1)))
            continue
        m = re.search(r"silence_end:\s*(-?[\d.]+)", linha)
        if m and inicio is not None:
            silencios.append((inicio, float(m.group(1))))
            inicio = None
    if inicio is not None:  # arquivo termina em silencio
        silencios.append((inicio, duracao))

    return silencios, duracao


def calcular_trechos(silencios, duracao):
    """Inverte os silencios em trechos de fala, com folga e limpeza."""
    trechos = []
    cursor = 0.0
    for ini, fim in silencios:
        if ini > cursor:
            trechos.append([cursor, ini])
        cursor = max(cursor, fim)
    if cursor < duracao:
        trechos.append([cursor, duracao])

    # folga: cada trecho come um pouco do silencio vizinho
    trechos = [[max(0.0, i - FOLGA), min(duracao, f + FOLGA)] for i, f in trechos]

    # funde trechos cujo corte entre eles ficou pequeno demais
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


# ── Resolve ─────────────────────────────────────────────────────────

def obter_resolve():
    r = globals().get("resolve")
    if r:
        return r
    try:
        bmd = globals().get("bmd")
        if bmd:
            return bmd.scriptapp("Resolve")
    except Exception:
        pass
    try:
        import DaVinciResolveScript as dvr
        return dvr.scriptapp("Resolve")
    except Exception:
        return None


def achar_clipe_alvo(projeto, mp):
    """Clipe selecionado no Media Pool; senao, o 1o clipe da timeline atual."""
    try:
        if hasattr(mp, "GetSelectedClips"):
            sel = mp.GetSelectedClips()
            if sel:
                clipes = list(sel.values()) if isinstance(sel, dict) else list(sel)
                if clipes and clipes[0]:
                    return clipes[0], "selecionado no Media Pool"
    except Exception:
        pass

    tl = projeto.GetCurrentTimeline()
    if tl:
        for trilha in ("video", "audio"):
            try:
                for n in range(1, int(tl.GetTrackCount(trilha)) + 1):
                    itens = tl.GetItemListInTrack(trilha, n)
                    if itens:
                        item = itens[0].GetMediaPoolItem()
                        if item:
                            return item, "1o clipe da timeline '%s'" % tl.GetName()
            except Exception:
                continue
    return None, None


def nome_timeline_livre(projeto, nome):
    usados = set()
    for i in range(1, int(projeto.GetTimelineCount()) + 1):
        try:
            usados.add(projeto.GetTimelineByIndex(i).GetName())
        except Exception:
            pass
    if nome not in usados:
        return nome
    n = 2
    while "%s %d" % (nome, n) in usados:
        n += 1
    return "%s %d" % (nome, n)


def montar_timeline(projeto, mp, item, trechos, fps, nome):
    nome = nome_timeline_livre(projeto, nome)
    tl = mp.CreateEmptyTimeline(nome)
    if not tl:
        raise RuntimeError("CreateEmptyTimeline('%s') retornou None" % nome)
    if not projeto.SetCurrentTimeline(tl):
        raise RuntimeError("nao consegui ativar a timeline nova")

    total_frames = None
    try:
        total_frames = int(float(item.GetClipProperty("Frames")))
    except Exception:
        pass

    subclipes = []
    for ini, fim in trechos:
        f_ini = int(round(ini * fps))
        f_fim = int(round(fim * fps)) - 1
        if total_frames:
            f_fim = min(f_fim, total_frames - 1)
        if f_fim > f_ini:
            subclipes.append({"mediaPoolItem": item, "startFrame": f_ini, "endFrame": f_fim})

    ok = 0
    LOTE = 50
    for i in range(0, len(subclipes), LOTE):
        parte = subclipes[i:i + LOTE]
        res = mp.AppendToTimeline(parte)
        if res:
            ok += len([x for x in res if x])
        log("  lote %d/%d anexado" % (i // LOTE + 1, (len(subclipes) + LOTE - 1) // LOTE))

    return nome, len(subclipes), ok


# ── Fluxos ──────────────────────────────────────────────────────────

def relatorio_trechos(arquivo):
    log("Analisando: %s" % arquivo)
    log("  (limiar %d dB, silencio minimo %.2fs, folga %.2fs)" % (SILENCIO_DB, SILENCIO_MIN, FOLGA))
    silencios, duracao = detectar_silencios(arquivo)
    trechos = calcular_trechos(silencios, duracao)

    mantido = sum(f - i for i, f in trechos)
    log("")
    log("Duracao: %s | silencios detectados: %d" % (fmt(duracao), len(silencios)))
    log("Trechos de fala mantidos: %d | %s (%.0f%% do total)"
        % (len(trechos), fmt(mantido), 100.0 * mantido / duracao if duracao else 0))
    log("Removido: %s" % fmt(duracao - mantido))
    log("")
    for n, (i, f) in enumerate(trechos, 1):
        log("  %3d. %s -> %s  (%.2fs)" % (n, fmt(i), fmt(f), f - i))
    return trechos, duracao


def rodar_no_resolve(r):
    projeto = r.GetProjectManager().GetCurrentProject()
    if not projeto:
        log("ERRO: nenhum projeto aberto no Resolve.")
        return
    mp = projeto.GetMediaPool()

    item, origem = achar_clipe_alvo(projeto, mp)
    if not item:
        log("ERRO: nao achei clipe. Selecione o clipe no Media Pool")
        log("      (ou abra uma timeline que contenha ele) e rode de novo.")
        return

    arquivo = item.GetClipProperty("File Path")
    if not arquivo or not os.path.isfile(arquivo):
        log("ERRO: nao achei o arquivo de midia do clipe ('%s')." % arquivo)
        return

    try:
        fps = float(item.GetClipProperty("FPS"))
    except Exception:
        fps = float(projeto.GetSetting("timelineFrameRate") or 30)

    log("Clipe: %s (%s)" % (item.GetName(), origem))
    log("FPS: %s" % fps)
    log("")

    trechos, duracao = relatorio_trechos(arquivo)
    if not trechos:
        log("")
        log("Nada a montar: nenhum trecho de fala sobrou. Confira SILENCIO_DB.")
        return

    log("")
    log("Montando a timeline nova...")
    base = os.path.splitext(item.GetName())[0]
    nome, pedidos, ok = montar_timeline(projeto, mp, item, trechos, fps, base + SUFIXO_TIMELINE)
    log("")
    log("PRONTO: timeline '%s' criada com %d/%d trechos." % (nome, ok, pedidos))
    if ok < pedidos:
        log("ATENCAO: %d trecho(s) nao anexaram — veja o log." % (pedidos - ok))
    log("O clipe e a timeline originais NAO foram alterados.")


def main():
    log("=" * 62)
    log("CORTE DE SILENCIO")
    log("=" * 62)
    r = obter_resolve()
    if r:
        try:
            rodar_no_resolve(r)
        except Exception as e:
            log("ERRO: %s" % e)
            import traceback
            log(traceback.format_exc())
    elif len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        log("(modo teste, sem Resolve — so mostra o que seria cortado)")
        log("")
        relatorio_trechos(sys.argv[1])
    else:
        log("Sem conexao com o Resolve e sem arquivo de teste.")
        log("No Resolve: menu Workspace > Scripts. No terminal: passe um video.")
    salvar_log()
    log("")
    log("Log salvo em: %s" % LOG)


main()
