"""
DIAGNÓSTICO — o que o DaVinci Resolve free permite via script interno.

100% LEITURA. Não cria, não altera e não apaga NADA no seu projeto.

COMO RODAR:
  1. Copie este arquivo para:
     %APPDATA%\\Blackmagic Design\\DaVinci Resolve\\Support\\Fusion\\Scripts\\Utility\\
  2. No Resolve: menu Workspace > Scripts > 00_diagnostico
  3. Ele grava o relatório no caminho definido em SAIDA abaixo.

Se o menu não listar o script, feche e reabra o Resolve.

⚠️ Este arquivo é uma CÓPIA — o original vive no repositório clonado (caminho
em SAIDA, abaixo). Ao editar, edite o original e reinstale, senão a cópia do
Resolve fica velha.

⚠️ EDITE SAIDA abaixo pro caminho onde VOCÊ clonou este repositório — o script
roda copiado pra outra pasta do Resolve, então não dá pra descobrir o caminho
sozinho (__file__ apontaria pra pasta Utility do Resolve, não pro repositório).
"""

import os
import sys
import platform

SAIDA = r"C:\CAMINHO\PARA\davinci-resolve-mcp\_diagnostico_resolve.txt"

linhas = []


def log(txt=""):
    linhas.append(str(txt))


def checa(obj, nome_metodo):
    """Reporta se um método existe no objeto (sem executá-lo)."""
    existe = hasattr(obj, nome_metodo)
    log(f"  {'SIM ' if existe else 'NAO '} {nome_metodo}")
    return existe


log("=" * 62)
log("DIAGNOSTICO — DaVinci Resolve via script interno")
log("=" * 62)

# ── Ambiente Python ────────────────────────────────────────────────
log("\n[AMBIENTE PYTHON]")
log(f"  versao: {sys.version.split()[0]}")
log(f"  executavel: {sys.executable}")
log(f"  plataforma: {platform.platform()}")

# subprocess é essencial: é como eu chamaria o ffmpeg de dentro do script
try:
    import subprocess
    log("  subprocess: SIM (da pra chamar ffmpeg de dentro do Resolve)")
except Exception as e:
    log(f"  subprocess: NAO ({e})")

# ── Conexão ────────────────────────────────────────────────────────
log("\n[CONEXAO]")
try:
    resolve  # type: ignore[name-defined]  # Resolve injeta esse global
    log("  'resolve' ja veio pronto como variavel global")
except NameError:
    try:
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp("Resolve")
        log("  'resolve' obtido via DaVinciResolveScript.scriptapp()")
    except Exception as e:
        log(f"  FALHOU ao obter 'resolve': {e}")
        resolve = None

if resolve is None:
    log("\n>>> SEM CONEXAO. Nada mais pode ser testado.")
else:
    # ── Versão / edição ────────────────────────────────────────────
    log("\n[VERSAO]")
    try:
        log(f"  versao: {resolve.GetVersionString()}")
    except Exception as e:
        log(f"  GetVersionString falhou: {e}")
    try:
        produto = resolve.GetProductName()
        log(f"  produto: {produto}")
        log(f"  >>> {'STUDIO (pago)' if 'Studio' in str(produto) else 'FREE (gratuito)'}")
    except Exception as e:
        log(f"  GetProductName falhou: {e}")
    try:
        log(f"  pagina atual: {resolve.GetCurrentPage()}")
    except Exception as e:
        log(f"  GetCurrentPage falhou: {e}")

    # ── Projeto ────────────────────────────────────────────────────
    log("\n[PROJETO ATUAL]")
    pm = None
    projeto = None
    try:
        pm = resolve.GetProjectManager()
        log(f"  ProjectManager: {'OK' if pm else 'None'}")
        projeto = pm.GetCurrentProject() if pm else None
        if projeto:
            log(f"  projeto aberto: {projeto.GetName()}")
            log(f"  timelines: {projeto.GetTimelineCount()}")
            for k in ("timelineFrameRate", "timelineResolutionWidth", "timelineResolutionHeight"):
                log(f"  {k}: {projeto.GetSetting(k)}")
        else:
            log("  nenhum projeto aberto")
    except Exception as e:
        log(f"  ERRO: {e}")

    # ── APIs para MONTAGEM EM LOTE (criar projeto/timelines) ───────
    log("\n[LOTE: criar projeto, importar, criar timelines]")
    if pm:
        for m in ("CreateProject", "LoadProject", "GetProjectListInCurrentFolder", "SaveProject"):
            checa(pm, m)
    mp = None
    try:
        mp = projeto.GetMediaPool() if projeto else None
        if mp:
            for m in ("ImportMedia", "CreateEmptyTimeline", "CreateTimelineFromClips",
                      "AppendToTimeline", "GetRootFolder", "AddSubFolder", "DeleteTimelines"):
                checa(mp, m)
    except Exception as e:
        log(f"  MediaPool ERRO: {e}")
    try:
        ms = resolve.GetMediaStorage()
        if ms:
            for m in ("AddItemListToMediaPool", "GetFileList", "GetMountedVolumeList"):
                checa(ms, m)
    except Exception as e:
        log(f"  MediaStorage ERRO: {e}")

    # ── APIs para CORTE DE SILENCIO ────────────────────────────────
    # A tecnica: detectar silencio com ffmpeg, e MONTAR uma timeline nova
    # so com os trechos com audio (AppendToTimeline aceita startFrame/endFrame).
    log("\n[CORTE DE SILENCIO]")
    log("  (tecnica: ffmpeg detecta silencio -> AppendToTimeline com subclipes)")
    tl = None
    try:
        tl = projeto.GetCurrentTimeline() if projeto else None
        if tl:
            log(f"  timeline atual: {tl.GetName()}")
            for m in ("GetItemListInTrack", "GetTrackCount", "GetStartFrame",
                      "GetEndFrame", "AddMarker", "SetSetting", "GetSetting"):
                checa(tl, m)
        else:
            log("  nenhuma timeline aberta (abra uma pra testar mais fundo)")
    except Exception as e:
        log(f"  ERRO: {e}")

    # ── APIs de LEGENDA ────────────────────────────────────────────
    log("\n[LEGENDA]")
    if tl:
        for m in ("CreateSubtitlesFromAudio", "ImportSubtitle", "GetTrackCount"):
            checa(tl, m)
        try:
            log(f"  faixas de legenda existentes: {tl.GetTrackCount('subtitle')}")
        except Exception as e:
            log(f"  GetTrackCount('subtitle') falhou: {e}")
    log("  (CreateSubtitlesFromAudio e Studio-only; importar SRT funciona no free)")

    # ── APIs de COR ────────────────────────────────────────────────
    log("\n[COR]")
    if tl:
        try:
            itens = tl.GetItemListInTrack("video", 1)
            if itens:
                it = itens[0]
                log(f"  testando no clipe: {it.GetName()}")
                for m in ("SetCDL", "SetLUT", "GetNodeGraph", "ApplyArriCdlLut",
                          "GetNumNodes", "SetProperty", "GetProperty"):
                    checa(it, m)
            else:
                log("  sem clipes na trilha video 1 (nao da pra testar cor)")
        except Exception as e:
            log(f"  ERRO: {e}")
    if projeto:
        for m in ("ApplyGradeFromDRX", "GetGallery", "GetCurrentTimeline"):
            checa(projeto, m)

    # ── APIs de AUDIO ──────────────────────────────────────────────
    log("\n[AUDIO]")
    if tl:
        for m in ("GetVoiceIsolationState", "SetVoiceIsolationState",
                  "GetTrackCount", "SetTrackName"):
            checa(tl, m)
    log("  (Voice Isolation e Studio-only; correcao L/R e ruido -> via ffmpeg)")

log("\n" + "=" * 62)
log("FIM")
log("=" * 62)

# ── Grava o relatório ──────────────────────────────────────────────
texto = "\n".join(linhas)
try:
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(texto)
    print(texto)
    print(f"\n\nRelatorio salvo em: {SAIDA}")
except Exception as e:
    print(texto)
    print(f"\n\nNAO consegui salvar em {SAIDA}: {e}")
