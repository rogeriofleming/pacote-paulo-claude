"""
CORTE DO "NE" — acha cada "ne" falado (via Whisper) e monta uma timeline sem eles.

Funciona no Resolve FREE porque roda POR DENTRO (menu Workspace > Scripts).
A tecnica em 3 passos:
  1. transcrever_palavras.py (no venv do projeto) transcreve o video com
     timestamp POR PALAVRA e salva "<video>.palavras.json" ao lado do video;
  2. este script acha as palavras da lista PALAVRAS_CORTAR no JSON;
  3. monta uma timeline nova ("<clipe> - SEM NE") com AppendToTimeline,
     pulando os intervalos dessas palavras.

O ORIGINAL NAO E TOCADO: nem o arquivo, nem a timeline existente.

TRANSCRICAO E DEMORADA (modelo medium na CPU: video de 10 min ~ 6 min).
Se o JSON nao existir, este script chama o venv e o Resolve fica ocupado
esperando. RECOMENDADO: gerar o JSON ANTES, num terminal:
  cd "C:\\CAMINHO\\PARA\\davinci-resolve-mcp"
  .venv\\Scripts\\python.exe scripts_resolve\\transcrever_palavras.py "D:\\caminho\\video.mp4"
Com o JSON pronto, o corte no Resolve e instantaneo.

COMO USAR NO RESOLVE:
  1. Instale com instalar_scripts.bat
  2. Selecione o clipe no Media Pool (ou deixe como 1o clipe da timeline atual)
  3. Menu Workspace > Scripts > 20_cortar_ne

AJUSTES:
  PALAVRAS_CORTAR — o que remover. Aceita mais muletas: ["ne", "tipo", "ai"].
                    Comparacao ignora acento, maiuscula e pontuacao
                    ("Ne?", "ne," e "NE" contam) e e por palavra INTEIRA
                    ("nem", "nesse" NUNCA casam).
  FOLGA_ANTES / FOLGA_DEPOIS — margem extra cortada em volta da palavra.
  TRECHO_MIN — sobra de fala menor que isso entre dois cortes e removida junto.

TESTE SEM RESOLVE (mostra o que seria cortado, nao mexe em nada):
  python 20_cortar_ne.py "D:\\caminho\\video.mp4"

⚠️ Este arquivo e uma COPIA quando instalado — o original vive no repositorio
clonado, em scripts_resolve/. Edite o original e reinstale.

⚠️ EDITE COFRE abaixo pro caminho onde VOCE clonou este repositorio — o script
roda copiado pra outra pasta do Resolve, entao nao da pra descobrir o caminho
do repositorio sozinho.
"""

import json
import os
import subprocess
import sys
import unicodedata

# ── Ajustes ─────────────────────────────────────────────────────────
PALAVRAS_CORTAR = ["ne"]   # sem acento: a comparacao ja ignora acentos
FOLGA_ANTES = 0.05         # s cortados antes da palavra
FOLGA_DEPOIS = 0.06        # s cortados depois da palavra
TRECHO_MIN = 0.15          # s; sobra de fala menor que isso vai junto no corte

SUFIXO_TIMELINE = " - SEM NE"
COFRE = r"C:\CAMINHO\PARA\davinci-resolve-mcp"
VENV_PY = os.path.join(COFRE, ".venv", "Scripts", "python.exe")
HELPER = os.path.join(COFRE, "scripts_resolve", "transcrever_palavras.py")
LOG = os.path.join(COFRE, "_corte_ne_log.txt")

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


# ── Deteccao ────────────────────────────────────────────────────────

def normalizar(palavra):
    """minusculas, sem acento, sem pontuacao — 'Né?,' -> 'ne'."""
    s = unicodedata.normalize("NFD", palavra.strip().lower())
    return "".join(c for c in s if c.isalnum())


def garantir_json(arquivo):
    """Retorna o caminho do JSON de palavras, transcrevendo se preciso."""
    caminho = arquivo + ".palavras.json"
    if os.path.isfile(caminho) and os.path.getmtime(caminho) >= os.path.getmtime(arquivo):
        log("Transcricao ja existe: %s" % os.path.basename(caminho))
        return caminho

    if not os.path.isfile(VENV_PY):
        raise RuntimeError("venv nao encontrado em %s" % VENV_PY)
    log("Transcrevendo agora (DEMORA — modelo medium na CPU roda a ~1.7x)...")
    log("Dica: da proxima vez gere o JSON antes, num terminal (ver cabecalho).")
    proc = subprocess.run([VENV_PY, HELPER, arquivo], capture_output=True, text=True)
    if proc.stdout:
        log(proc.stdout.strip())
    if proc.returncode != 0:
        raise RuntimeError("transcricao falhou:\n%s" % (proc.stderr or "")[-800:])
    if not os.path.isfile(caminho):
        raise RuntimeError("transcricao rodou mas o JSON nao apareceu: %s" % caminho)
    return caminho


def achar_cortes(arquivo):
    """Le o JSON e devolve (cortes [(ini,fim,palavra)], duracao, total_palavras)."""
    with open(garantir_json(arquivo), encoding="utf-8") as f:
        dados = json.load(f)

    alvos = {normalizar(p) for p in PALAVRAS_CORTAR}
    cortes = []
    for w in dados["palavras"]:
        if normalizar(w["palavra"]) in alvos:
            cortes.append((max(0.0, w["inicio"] - FOLGA_ANTES),
                           min(dados["duracao"], w["fim"] + FOLGA_DEPOIS),
                           w["palavra"].strip()))
    return cortes, dados["duracao"], len(dados["palavras"])


def calcular_trechos(cortes, duracao):
    """Inverte os cortes em trechos mantidos; sobra minuscula entre cortes sai junto."""
    # funde cortes que se encostam
    fundidos = []
    for ini, fim, _ in sorted(cortes):
        if fundidos and ini - fundidos[-1][1] < TRECHO_MIN:
            fundidos[-1][1] = max(fundidos[-1][1], fim)
        else:
            fundidos.append([ini, fim])

    trechos = []
    cursor = 0.0
    for ini, fim in fundidos:
        if ini - cursor >= TRECHO_MIN:
            trechos.append((cursor, ini))
        cursor = max(cursor, fim)
    if duracao - cursor >= TRECHO_MIN:
        trechos.append((cursor, duracao))
    return trechos


def fmt(seg):
    m, s = divmod(seg, 60)
    return "%02d:%06.3f" % (int(m), s)


# ── Resolve (mesmo padrao do 10_cortar_silencio) ────────────────────

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

def relatorio(arquivo):
    log("Analisando: %s" % arquivo)
    log("Palavras a cortar: %s (folga -%.2fs/+%.2fs)"
        % (", ".join(PALAVRAS_CORTAR), FOLGA_ANTES, FOLGA_DEPOIS))
    log("")
    cortes, duracao, total = achar_cortes(arquivo)
    trechos = calcular_trechos(cortes, duracao)

    log("Palavras transcritas: %d | ocorrencias a cortar: %d" % (total, len(cortes)))
    for n, (i, f, p) in enumerate(cortes, 1):
        log("  %3d. %s -> %s  '%s'" % (n, fmt(i), fmt(f), p))
    removido = duracao - sum(f - i for i, f in trechos)
    log("")
    log("Duracao: %s | removido: %s | trechos mantidos: %d"
        % (fmt(duracao), fmt(removido), len(trechos)))
    return trechos


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

    trechos = relatorio(arquivo)
    if not trechos:
        log("Nenhuma ocorrencia encontrada — nada a cortar.")
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
    log("CORTE DO 'NE'")
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
        relatorio(sys.argv[1])
    else:
        log("Sem conexao com o Resolve e sem arquivo de teste.")
        log("No Resolve: menu Workspace > Scripts. No terminal: passe um video.")
    salvar_log()
    log("")
    log("Log salvo em: %s" % LOG)


main()
