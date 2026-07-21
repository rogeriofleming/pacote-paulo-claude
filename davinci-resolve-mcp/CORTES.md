# CORTES.md — corte de silêncio e corte do "né" no Resolve free

> Dois scripts de menu que montam uma **timeline nova já
> cortada** — sem tocar no arquivo original nem na timeline existente.
> Funcionam no Resolve **free** porque rodam por dentro (Workspace > Scripts),
> não por conexão externa (a que o free bloqueia — ver `WINDOWS_SETUP.md` §1).
>
> ⚠️ **Status:** a parte de análise (detecção de silêncio e de "né") foi
> testada e verificada em Windows 11 + Resolve free. A parte que monta a
> timeline (`AppendToTimeline` por dentro do free) merece confirmar no seu
> primeiro uso real. Se falhar, rode `00_diagnostico` primeiro pra isolar a causa.

## Instalação (uma vez por máquina)

Rodar `scripts_resolve\instalar_scripts.bat` (duplo clique). Ele copia os
scripts de menu pra pasta Utility do Resolve. Resolve aberto → fechar e reabrir
pra aparecer no menu.

> Os instalados são CÓPIAS. Editou o original neste repositório → rodar o .bat de novo.

## 1. Cortar silêncios — `10_cortar_silencio`

1. No Resolve, **selecionar o clipe no Media Pool** (ou deixá-lo como 1º clipe
   da timeline atual).
2. Menu **Workspace > Scripts > 10_cortar_silencio**.
3. Sai uma timeline nova **"\<clipe\> - SEM SILENCIO"**, já aberta, só com os
   trechos falados.

Como funciona: ffmpeg (`silencedetect`) acha os silêncios no arquivo de mídia;
o script monta a timeline com subclipes dos trechos com som.

Ajustes no topo do script (editar neste repositório e reinstalar):

| Constante | Padrão | O que faz |
|---|---|---|
| `SILENCIO_DB` | -34 | abaixo disso é silêncio; ambiente barulhento → -28 |
| `SILENCIO_MIN` | 0.60s | silêncio mais curto que isso fica no vídeo |
| `FOLGA` | 0.12s | respiro mantido em cada borda do corte |
| `CORTE_MIN` | 0.25s | corte que ficaria menor que isso nem é feito |

## 2. Cortar os "né" — `20_cortar_ne`

**Passo A (recomendado, fora do Resolve):** gerar a transcrição por palavra —
é a parte demorada (modelo `medium` na CPU ≈ 1,7×: vídeo de 10 min ≈ 6 min):

```
cd "C:\CAMINHO\PARA\davinci-resolve-mcp"
.venv\Scripts\python.exe scripts_resolve\transcrever_palavras.py "D:\caminho\video.mp4"
```

Isso salva `video.mp4.palavras.json` ao lado do vídeo (todas as palavras com
tempos — mudar a lista de palavras depois **não** exige retranscrever).

**Passo B (no Resolve):** selecionar o clipe → **Workspace > Scripts >
20_cortar_ne** → sai a timeline **"\<clipe\> - SEM NE"**. Se o JSON não existir,
o script transcreve na hora (e o Resolve fica ocupado esperando).

Ajustes no topo do script:

| Constante | Padrão | O que faz |
|---|---|---|
| `PALAVRAS_CORTAR` | `["ne"]` | pode virar `["ne", "tipo", "ai"]`; ignora acento/maiúscula/pontuação e só casa palavra inteira ("nem"/"nesse" nunca caem) |
| `FOLGA_ANTES` / `FOLGA_DEPOIS` | 0.05s / 0.06s | margem cortada em volta da palavra |
| `TRECHO_MIN` | 0.15s | sobra de fala menor que isso entre dois cortes sai junto |

> O helper usa `initial_prompt` de transcrição **literal** — sem ele o Whisper
> "limpa" os vícios de linguagem e os "né" somem da transcrição.

## Testar sem o Resolve (só mostra o que cortaria, não mexe em nada)

```
.venv\Scripts\python.exe scripts_resolve\10_cortar_silencio.py "video.mp4"
.venv\Scripts\python.exe scripts_resolve\20_cortar_ne.py "video.mp4"
```

## Verificação já feita (Windows 11 + Resolve free, áudio sintético de teste)

- **Silêncio:** áudio sintético com tons em 0–2s / 3,5–5,5s / 7–9s → os 3
  silêncios detectados e os 3 trechos mantidos saíram exatos, com a folga certa.
- **"né":** fala pt-BR sintetizada (voz do Windows) com 3 "né" no meio →
  Whisper `medium` transcreveu 33 palavras, os 3 "né" achados (inclusive "ne?"
  e "ne,"), "nunca" não casou, 0,87s marcados pra remoção.
- Arquivos de teste ficaram numa pasta `tmp/` local (fora do git) — reproduza
  o teste na sua máquina antes de confiar em vídeo real.

## Limites conhecidos

- Processam **um clipe** por vez (o selecionado / 1º da timeline). Vídeo
  gravado em vários arquivos → rodar uma vez por arquivo e juntar as timelines.
- O corte é por **remontagem**: a timeline nova nasce só com Video 1 + áudio do
  clipe. Efeitos/cor aplicados na timeline velha não migram (no clipe, sim).
- Logs de cada execução: `_corte_silencio_log.txt` e `_corte_ne_log.txt` na
  raiz deste repositório.
