"""
LEGENDA QUEIMADA — vários estilos, 100% fora do Resolve (ffmpeg puro).

Roda no venv do projeto (processamento externo, como o transcrever_palavras.py):

  .venv\\Scripts\\python.exe scripts_resolve\\30_legenda_reels.py "video.mp4"
  .venv\\Scripts\\python.exe scripts_resolve\\30_legenda_reels.py "video.mp4" --estilo palavra

Consome o mesmo "<video>.palavras.json" da transcrição (gera na hora se faltar),
monta um .ass com o estilo escolhido e QUEIMA a legenda no vídeo. O original
NÃO é tocado — sai "<video> - LEGENDADO.mp4".

ESTILOS (--estilo, ou --listar-estilos pra ver todos):
  karaoke      blocos curtos, a palavra falada acende (padrão)
  palavra      uma palavra grande por vez, centralizada (viral)
  pop          uma palavra por vez com "salto" de escala na entrada
  bloco        legenda clássica de 2 linhas na base, discreta
  keyword      frase branca, a palavra-chave do trecho destacada
  minimalista  fonte fina, branca, sem caixa alta, discreta

EDITAR: o .ass fica ao lado do vídeo (texto puro). Edite e rode de novo — ele
respeita a edição (requeima sem retranscrever). --regerar refaz do zero.
Mudar de estilo depois de editar exige --regerar (o estilo mora no .ass).

TESTE: python 30_legenda_reels.py --autoteste
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from glob import glob

# raiz do projeto (um nivel acima de scripts_resolve)
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Estilos ─────────────────────────────────────────────────────────
# Cada estilo é um preset. Cores em RRGGBB. "agrup": bloco|palavra.
# "efeito": karaoke|pop|keyword|none.
ESTILOS = {
    "karaoke": dict(
        fonte="Arial", negrito=True, tam_pct=8.5, maiusc=True,
        cor="FFFFFF", cor2="22DDFF", contorno_cor="000000", contorno=3.2, sombra=1.4,
        pos="baixo", margem_pct=14.0, agrup="bloco", efeito="karaoke",
        max_palavras=4, max_seg=2.5),
    "palavra": dict(
        fonte="Arial", negrito=True, tam_pct=13.0, maiusc=True,
        cor="FFFFFF", cor2="FFFFFF", contorno_cor="000000", contorno=4.0, sombra=1.6,
        pos="centro", margem_pct=0.0, agrup="palavra", efeito="none",
        max_palavras=1, max_seg=1.5),
    "pop": dict(
        fonte="Arial", negrito=True, tam_pct=13.0, maiusc=True,
        cor="FFEE22", cor2="FFEE22", contorno_cor="000000", contorno=4.2, sombra=1.6,
        pos="centro", margem_pct=0.0, agrup="palavra", efeito="pop",
        max_palavras=1, max_seg=1.5),
    "bloco": dict(
        fonte="Arial", negrito=True, tam_pct=5.2, maiusc=False,
        cor="FFFFFF", cor2="FFFFFF", contorno_cor="000000", contorno=2.0, sombra=1.0,
        pos="baixo", margem_pct=8.0, agrup="bloco", efeito="none",
        max_palavras=8, max_seg=3.5),
    "keyword": dict(
        fonte="Arial", negrito=True, tam_pct=8.5, maiusc=True,
        cor="FFFFFF", cor2="FFDD22", contorno_cor="000000", contorno=3.2, sombra=1.4,
        pos="baixo", margem_pct=14.0, agrup="bloco", efeito="keyword",
        max_palavras=4, max_seg=2.5),
    "minimalista": dict(
        fonte="Arial", negrito=False, tam_pct=5.0, maiusc=False,
        cor="FFFFFF", cor2="FFFFFF", contorno_cor="000000", contorno=1.2, sombra=0.6,
        pos="baixo", margem_pct=10.0, agrup="bloco", efeito="none",
        max_palavras=7, max_seg=3.5),
}

PAUSA_QUEBRA = 0.50        # pausa entre palavras >= isso força novo bloco
KARAOKE_CS_MIN = 1         # duração mínima de um trecho karaokê (centésimos)

SUFIXO = " - LEGENDADO"
LOG = os.path.join(_BASE, "_legenda_reels_log.txt")

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
    """(largura, altura) JÁ considerando a rotação (o que aparece na tela).

    Celular na vertical grava 3840x2160 com rotação 90/270 -> na tela é 2160x3840.
    Sem isso, a fonte (% da altura) sai no tamanho errado em vídeo vertical.
    """
    fp = _achar_bin("ffprobe")
    w = h = rot = None
    if fp:
        try:
            out = subprocess.run(
                [fp, "-v", "error", "-select_streams", "v:0", "-show_entries",
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
    if w is None:
        out = subprocess.run([achar_ffmpeg(), "-nostdin", "-hide_banner", "-i", arquivo],
                             capture_output=True, text=True).stderr
        m = re.search(r",\s*(\d{2,5})x(\d{2,5})", out)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
        mr = re.search(r"rotate\s*:\s*(-?\d+)", out)
        if mr:
            rot = int(mr.group(1))
    if w is None:
        log("AVISO: nao consegui ler a resolucao — assumindo 1080x1920.")
        return 1080, 1920
    if rot and abs(rot) % 180 == 90:
        w, h = h, w
    return w, h


# ── Transcrição (reusa o motor do projeto) ──────────────────────────

def garantir_palavras(video):
    jpath = video + ".palavras.json"
    if os.path.isfile(jpath):
        log("Usando transcricao existente: %s" % os.path.basename(jpath))
        with open(jpath, encoding="utf-8") as f:
            return json.load(f).get("palavras", [])

    log("Sem JSON de palavras — transcrevendo agora (pode demorar)...")
    sys.path.insert(0, os.path.join(_BASE, "src"))
    import importlib.util
    tp = os.path.join(_BASE, "scripts_resolve", "transcrever_palavras.py")
    spec = importlib.util.spec_from_file_location("transcrever_palavras", tp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    dados = mod.transcrever(video, os.environ.get("WHISPER_MODEL", "medium"))
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    log("Transcricao salva: %s (%d palavras)" % (jpath, len(dados["palavras"])))
    return dados["palavras"]


# ── Agrupamento ─────────────────────────────────────────────────────

def limpar(palavras):
    out = []
    for p in palavras:
        txt = (p.get("palavra") or "").strip()
        if txt:
            out.append({"inicio": float(p["inicio"]), "fim": float(p["fim"]), "palavra": txt})
    return out


def agrupar_blocos(palavras, est):
    blocos, atual = [], []
    for p in palavras:
        if atual:
            gap = p["inicio"] - atual[-1]["fim"]
            dur = p["fim"] - atual[0]["inicio"]
            if (len(atual) >= est["max_palavras"] or dur > est["max_seg"]
                    or gap >= PAUSA_QUEBRA):
                blocos.append(atual)
                atual = []
        atual.append(p)
    if atual:
        blocos.append(atual)
    return blocos


# ── Geração do .ass ─────────────────────────────────────────────────

def _ass_cor(rrggbb):
    """RRGGBB -> &H00BBGGRR (ASS é BGR, AA=00 opaco)."""
    return "&H00%s%s%s" % (rrggbb[4:6], rrggbb[2:4], rrggbb[0:2])


def _ass_tempo(seg):
    seg = max(0.0, seg)
    h = int(seg // 3600)
    m = int((seg % 3600) // 60)
    return "%d:%02d:%05.2f" % (h, m, seg % 60)


def _txt(w, est):
    t = w["palavra"].upper() if est["maiusc"] else w["palavra"]
    return t.replace("{", "(").replace("}", ")")


def _evento(ini, fim, texto):
    return "Dialogue: 0,%s,%s,Leg,,0,0,0,,%s" % (_ass_tempo(ini), _ass_tempo(fim), texto)


def gerar_ass(palavras, larg, alt, est, caminho_ass):
    tam = max(12, int(round(alt * est["tam_pct"] / 100.0)))
    margem_v = int(round(alt * est["margem_pct"] / 100.0))
    align = {"baixo": 2, "centro": 5, "alto": 8}.get(est["pos"], 2)

    header = [
        "[Script Info]", "ScriptType: v4.00+",
        "PlayResX: %d" % larg, "PlayResY: %d" % alt,
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding",
        "Style: Leg,%s,%d,%s,%s,%s,&H64000000,%d,0,0,0,100,100,0,0,1,%.1f,%.1f,%d,"
        "80,80,%d,1" % (
            est["fonte"], tam, _ass_cor(est["cor"]), _ass_cor(est["cor2"]),
            _ass_cor(est["contorno_cor"]), -1 if est["negrito"] else 0,
            est["contorno"], est["sombra"], align, margem_v),
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    eventos = []
    efeito = est["efeito"]

    if est["agrup"] == "palavra":
        # um evento por palavra
        for i, w in enumerate(palavras):
            fim = w["fim"]
            # segura a palavra até a próxima (evita piscar entre palavras coladas)
            if i + 1 < len(palavras) and palavras[i + 1]["inicio"] - w["fim"] < 0.25:
                fim = palavras[i + 1]["inicio"]
            txt = _txt(w, est)
            if efeito == "pop":
                txt = "{\\fscx55\\fscy55\\t(0,110,\\fscx100\\fscy100)}" + txt
            eventos.append(_evento(w["inicio"], fim, txt))
    else:
        blocos = agrupar_blocos(palavras, est)
        for bloco in blocos:
            ini, fim = bloco[0]["inicio"], bloco[-1]["fim"]
            if efeito == "karaoke":
                partes = []
                for w in bloco:
                    cs = max(KARAOKE_CS_MIN, int(round((w["fim"] - w["inicio"]) * 100)))
                    partes.append("{\\kf%d}%s" % (cs, _txt(w, est)))
                eventos.append(_evento(ini, fim, " ".join(partes)))
            elif efeito == "keyword":
                # destaca a palavra mais longa do bloco (heurística de "importante")
                idx = max(range(len(bloco)), key=lambda k: len(bloco[k]["palavra"]))
                partes = []
                for k, w in enumerate(bloco):
                    t = _txt(w, est)
                    if k == idx:
                        t = "{\\c%s}%s{\\c%s}" % (_ass_cor(est["cor2"]), t, _ass_cor(est["cor"]))
                    partes.append(t)
                eventos.append(_evento(ini, fim, " ".join(partes)))
            else:  # none — texto simples
                eventos.append(_evento(ini, fim, " ".join(_txt(w, est) for w in bloco)))

    with open(caminho_ass, "w", encoding="utf-8") as f:
        f.write("\n".join(header + eventos) + "\n")
    return len(eventos)


# ── Queima ──────────────────────────────────────────────────────────

def queimar(video, caminho_ass, saida):
    ff = achar_ffmpeg()
    ass_ff = caminho_ass.replace("\\", "/").replace(":", "\\:")
    cmd = [
        ff, "-nostdin", "-hide_banner", "-y", "-i", video,
        "-vf", "ass='%s'" % ass_ff,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "copy", "-movflags", "+faststart", saida,
    ]
    log("ffmpeg queimando a legenda...")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg falhou:\n%s" % proc.stderr[-800:])
    return saida


# ── Fluxo principal ─────────────────────────────────────────────────

def processar(video, estilo="karaoke", regerar=False):
    if not os.path.isfile(video):
        raise RuntimeError("Arquivo nao existe: %s" % video)
    if estilo not in ESTILOS:
        raise RuntimeError("Estilo '%s' nao existe. Opcoes: %s"
                           % (estilo, ", ".join(ESTILOS)))
    larg, alt = dimensoes_efetivas(video)
    log("Video: %s  (efetivo %dx%d) | estilo: %s"
        % (os.path.basename(video), larg, alt, estilo))

    base, _ = os.path.splitext(video)
    caminho_ass = base + ".legenda.ass"

    if os.path.isfile(caminho_ass) and not regerar:
        log("Usando .ass EXISTENTE (respeitando suas edicoes): %s"
            % os.path.basename(caminho_ass))
        log("  (pra trocar de estilo ou refazer da fala: --regerar)")
    else:
        palavras = limpar(garantir_palavras(video))
        if not palavras:
            raise RuntimeError("Nenhuma palavra na transcricao — nada a legendar.")
        n = gerar_ass(palavras, larg, alt, ESTILOS[estilo], caminho_ass)
        log("Palavras: %d  ->  .ass gerado: %s (%d linhas, estilo %s)"
            % (len(palavras), os.path.basename(caminho_ass), n, estilo))
        log("  (edite esse .ass e rode de novo pra ajustar sem retranscrever)")

    saida = base + SUFIXO + ".mp4"
    queimar(video, caminho_ass, saida)
    log("")
    log("PRONTO: %s" % saida)
    log("O video original NAO foi alterado.")
    return saida


# ── Autoteste ───────────────────────────────────────────────────────

def autoteste(estilo=None):
    estilos = [estilo] if estilo else list(ESTILOS)
    log("AUTOTESTE — video sintetico + JSON fake, estilos: %s" % ", ".join(estilos))
    ff = achar_ffmpeg()
    tmp = os.path.join(_BASE, "tmp")
    os.makedirs(tmp, exist_ok=True)
    video = os.path.join(tmp, "_autoteste_legenda.mp4")
    r = subprocess.run(
        [ff, "-nostdin", "-hide_banner", "-y",
         "-f", "lavfi", "-i", "color=c=0x223344:s=1080x1920:d=5",
         "-f", "lavfi", "-i", "sine=frequency=220:duration=5",
         "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", video], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg (video de teste) falhou:\n%s" % r.stderr[-500:])

    frase = "isso aqui e um teste de legenda estilo reels no davinci".split()
    palavras, t = [], 0.3
    for w in frase:
        palavras.append({"inicio": round(t, 2), "fim": round(t + 0.32, 2), "palavra": w})
        t += 0.40
    with open(video + ".palavras.json", "w", encoding="utf-8") as f:
        json.dump({"arquivo": video, "duracao": 5.0, "palavras": palavras},
                  f, ensure_ascii=False, indent=1)

    ok_all = True
    for est in estilos:
        ass = os.path.splitext(video)[0] + ".legenda.ass"
        if os.path.isfile(ass):
            os.remove(ass)
        saida = processar(video, estilo=est, regerar=True)
        # renomeia por estilo pra dar pra comparar
        alvo = os.path.splitext(video)[0] + "_" + est + ".mp4"
        try:
            if os.path.isfile(alvo):
                os.remove(alvo)
            os.replace(saida, alvo)
        except Exception:
            alvo = saida
        ok = os.path.isfile(alvo) and os.path.getsize(alvo) > 10000
        ok_all = ok_all and ok
        log("  estilo %-12s -> %s  %s"
            % (est, os.path.basename(alvo), "OK" if ok else "FALHOU"))
    log("")
    log("AUTOTESTE %s" % ("OK" if ok_all else "FALHOU"))
    return ok_all


def main():
    ap = argparse.ArgumentParser(description="Queima legenda em vários estilos (ffmpeg)")
    ap.add_argument("video", nargs="?", help="caminho do video")
    ap.add_argument("--estilo", default="karaoke", help="ver --listar-estilos")
    ap.add_argument("--regerar", action="store_true",
                    help="refaz o .ass do zero (troca de estilo / descarta edicoes)")
    ap.add_argument("--listar-estilos", action="store_true")
    ap.add_argument("--autoteste", action="store_true")
    args = ap.parse_args()

    if args.listar_estilos:
        for nome in ESTILOS:
            print("  %-12s" % nome)
        return

    log("=" * 62)
    log("LEGENDA (%s)" % args.estilo)
    log("=" * 62)
    try:
        if args.autoteste:
            autoteste(args.estilo if args.estilo != "karaoke" else None)
        elif args.video:
            processar(args.video, estilo=args.estilo, regerar=args.regerar)
        else:
            log("Passe um video, ou use --autoteste. Estilos: %s" % ", ".join(ESTILOS))
    except Exception as e:
        log("ERRO: %s" % e)
        import traceback
        log(traceback.format_exc())
    finally:
        salvar_log()
        log("Log salvo em: %s" % LOG)


if __name__ == "__main__":
    main()
