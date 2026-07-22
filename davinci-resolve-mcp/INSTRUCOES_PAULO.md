# Como usar este pacote — leia primeiro

Isto é um MCP (Model Context Protocol) que conecta o Claude ao DaVinci Resolve,
mais dois scripts extras (corte de silêncio e corte de vício de linguagem)
adaptados pra rodar no **Resolve free** no Windows, sem precisar do Studio.

## O que dá pra fazer

| Recurso | Precisa de Resolve Studio? |
|---|---|
| Transcrição local de vídeo/áudio (gera SRT pra importar como legenda) | ❌ Não |
| Screenshot da janela do Resolve | ❌ Não |
| Corte automático de silêncio (`10_cortar_silencio`) | ❌ Não (roda por dentro, via menu) |
| Corte automático de vício de linguagem tipo "né"/"tipo"/"aí" (`20_cortar_ne`) | ❌ Não (mesma lógica) |
| Os ~48 tools de controle direto do Resolve (mover clipe, aplicar LUT, renderizar, etc.) | ✅ Sim, exige Studio |

Ou seja: mesmo sem comprar o Studio, você já ganha transcrição/legenda automática
e os dois cortes automáticos — que costumam ser a parte mais chata e demorada
de editar.

## Jeito FÁCIL: um clique instala tudo (Windows)

Depois de clonar o repositório, entre na pasta `davinci-resolve-mcp` e **dê duplo
clique em `INSTALAR.bat`**. Ele faz sozinho: confere o Python, instala o `uv` e o
`ffmpeg` (build certo do gyan.dev) se faltarem, instala as dependências
(`faster-whisper` etc.), **baixa o modelo Whisper** e roda um autoteste pra provar
que a transcrição e o pipeline de vídeo funcionam. Se ele instalar o `uv`/`ffmpeg`,
peça pra você fechar e rodar o `INSTALAR.bat` **uma segunda vez** (o Windows só
enxerga programa novo num terminal novo) — a 2ª rodada termina tudo.

> macOS/Linux: rode `./instalar.sh` na mesma pasta (instala o `ffmpeg` você mesmo
> pelo `brew`/`apt` — o script avisa).

O que o instalador NÃO faz: registrar o MCP no seu Claude (isso é o `.mcp.json`,
passo 3 abaixo) e configurar o Resolve Studio (passo 5). O passo a passo manual
abaixo continua valendo se você preferir fazer à mão ou se algo falhar.

## Passo a passo de instalação

### 1. Pré-requisitos
- Python 3.10+ e [`uv`](https://astral.sh/uv/) instalados.
- DaVinci Resolve (free ou Studio) instalado.
- Windows: `winget install Gyan.FFmpeg` (necessário pra transcrição local — ver
  `WINDOWS_SETUP.md` §4 se aparecer erro de import do `faster-whisper`).

### 2. Instalar as dependências
```
cd caminho\onde\voce\clonou\davinci-resolve-mcp
uv sync --all-extras
```

### 3. Configurar o `.mcp.json`
```
copy .mcp.json.exemplo .mcp.json
```
Edite o `.mcp.json` recém-criado:
- `command`: caminho do `uv.exe` na sua máquina (`where uv` no PowerShell acha).
- `args` → segundo item de `--directory`: caminho absoluto onde você clonou esta pasta.
- As outras variáveis (`RESOLVE_SCRIPT_LIB` etc.) já vêm certas pra uma instalação
  padrão do Resolve no Windows.

Abrindo o Claude Code dentro desta pasta, o servidor MCP sobe sozinho.

### 4. Instalar os scripts de corte (opcional, mas é a parte mais útil no free)
1. Edite os 4 caminhos marcados com `⚠️ EDITE` nos arquivos dentro de
   `scripts_resolve/` (`00_diagnostico.py`, `10_cortar_silencio.py`,
   `20_cortar_ne.py`) — troque `C:\CAMINHO\PARA\davinci-resolve-mcp` pelo
   caminho real onde você clonou este repositório.
2. Rode `scripts_resolve\instalar_scripts.bat` (duplo clique). Isso copia os
   scripts pra pasta de Scripts do Resolve.
3. Feche e reabra o Resolve — os scripts aparecem em **Workspace > Scripts**.
4. Leia `CORTES.md` pro passo a passo de uso de cada corte.

### 5. Ajustar o vocabulário pro SEU conteúdo (recomendado)
Edite `vocabulario/nomes.txt` e `vocabulario/correcoes.txt` com os nomes
próprios, marcas e termos que aparecem no que você grava — os dois arquivos já
vêm com exemplo e explicação de como preencher. Isso é o que faz o Whisper
acertar nomes que ele nunca viu antes.

## Se algo travar

Rode o script de menu `00_diagnostico` primeiro — ele só LÊ o estado do Resolve
(não altera nada) e mostra exatamente o que está e o que não está funcionando.
`WINDOWS_SETUP.md` documenta os bloqueios mais comuns (Resolve free vs Studio,
Smart App Control) e como cada um foi resolvido.

## Créditos

Este projeto é um fork do [`barckley75/resolve-claude-mcp`](https://github.com/barckley75/resolve-claude-mcp)
(MIT — ver `LICENSE`), originalmente feito pra macOS. `WINDOWS_SETUP.md` documenta
tudo que foi adaptado pra rodar no Windows.
