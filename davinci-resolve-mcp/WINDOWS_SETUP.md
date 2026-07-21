# Windows + Claude Code — o que foi adaptado e o que foi verificado

Fork de [`barckley75/resolve-claude-mcp`](https://github.com/barckley75/resolve-claude-mcp)
(feito pra macOS + Claude Desktop + Resolve Studio), adaptado pra
**Windows + Claude Code + Resolve free**. Este doc registra o que foi testado de
verdade (Windows 11, Resolve free) — e o que continua bloqueado, com a causa provada.

> **Origem:** clonado do upstream no commit `9398758` ("Add LICENSE; rename display
> name to Resolve Claude MCP"). Se você quiser comparar com o upstream ou puxar
> atualização dele, clone de novo em outro lugar e use `diff`.

---

## 1. O bloqueio principal: scripting externo é só no Studio

**A versão FREE do DaVinci Resolve não aceita conexão de processo externo.**
É isso que qualquer MCP precisa fazer. Não tem contorno em código — o bloqueio
está no Resolve, não no servidor.

Checagens que confirmam o bloqueio (rode na sua máquina se quiser confirmar de novo):

| Checagem | Resultado esperado no free |
|---|---|
| `fusionscript.dll`, pasta Scripting, Modules existem | ✅ existem mesmo no free |
| Resolve rodando | ✅ |
| `import DaVinciResolveScript` | ✅ a DLL carrega |
| `scriptapp("Resolve")` | ❌ retorna `None` no free |
| `scriptapp("Fusion")` | ❌ retorna `None` no free |
| `System.Scripting.Mode` no `config.dat` | pode já estar `1` (Local) e mesmo assim recusar |
| Menu "External scripting using" em Preferences | **não existe** no free (só no Studio) |

O menu some no free porque o recurso não existe nele. A opção de config existe
no arquivo, mas ligá-la não adianta — o binário recusa a conexão externa.

> O README oficial da Blackmagic (instalado em
> `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\README.txt`)
> diz que as APIs são "superset comum pra Free e Studio". Isso vale pras **funções**
> da API, não pra **capacidade de conectar de fora** — essa é Studio-only.
> Confirmado no fórum da Blackmagic e na doc da API.

**Consequência:** os ~48 tools de controle do Resolve só funcionam com
**DaVinci Resolve Studio** (licença vitalícia, US$ 295, pagamento único).

---

> **A brecha do free:** o bloqueio é só pra conexão **externa**. Script rodado
> **pelo menu** (Workspace > Scripts) roda por dentro do Resolve. É por essa
> porta que entram o corte de silêncio e o corte de vício de linguagem —
> uso e ajustes em [`CORTES.md`](CORTES.md).

## 2. O que FUNCIONA hoje, mesmo no Resolve free

Estes tools não tocam a API de scripting, então rodam sem Studio:

- **`transcribe_audio`** e **`export_srt`** — caminho completo de legenda:
  transcreve local → SRT → importar no Resolve (`File > Import > Subtitle`),
  que funciona no free.
- **`screenshot`** — captura a janela do Resolve, sem depender da API de scripting.
- `list_whisper_models` — lista os modelos, sem dependência.

`transcribe_and_add_subtitles` **não** entra nessa lista: ele escreve marcadores
na timeline, então precisa do Studio.

---

## 3. Mudanças feitas no código (upstream → este fork)

### Screenshot (era macOS-only → agora cross-platform)
`server.py`

- macOS: mantido (`Quartz` + `screencapture`).
- Windows: novo caminho com `pywin32` (acha a janela pelo título) + `mss`
  (captura a região) + `mss.tools.to_png` (encode, sem precisar de Pillow).
- `_capture_screenshot()` agora despacha por plataforma.

**Detalhe que custou duas tentativas:** captura de região pega o que está
*visível* na tela. Com o Resolve atrás de outra janela, vinha a janela errada.
Pior: `SetForegroundWindow` sozinho **falha silenciosamente** quando chamado de
um processo que não detém o foreground (restrição do Windows). A correção foi
`AttachThreadInput` via `ctypes` — anexa temporariamente à thread do foreground,
o que libera o `SetForegroundWindow`. Com isso a captura passou a trazer o
Resolve pra frente e fotografá-lo de fato.

### Transcrição (era Apple-only → agora tem backend pra Windows)
`transcription.py`

- Backend escolhido em runtime: `mlx-whisper` no macOS, **`faster-whisper`** no
  resto (CTranslate2; CPU ou CUDA). Mesmos pesos do Whisper da OpenAI, mesma
  acurácia — muda só o motor.
- O caminho faster-whisper não precisa do chunking com ffmpeg (ele decodifica e
  streama segmentos sozinho). O chunking do mlx foi preservado.
- `turbo`/`large` → `large-v3` (id que sempre resolve nas versões do
  faster-whisper). Nome desconhecido passa direto.

### Dependências
`pyproject.toml` — `mss` (não-macOS), `pywin32` (Windows), `faster-whisper`
(não-macOS, no extra `transcription`).

---

## 4. Transcrição local: como resolver o bloqueio do Smart App Control

**Funciona, sem Studio e sem mexer na segurança do Windows.**

### O problema

Em máquinas com **Smart App Control** ligado (padrão em instalações novas do
Windows 11), `import faster_whisper` pode morrer com:

```
ImportError: DLL load failed while importing codeccontext:
Uma política de Controle de Aplicativo bloqueou este arquivo.
```

Causa (confirmável em qualquer máquina com o mesmo sintoma):

- `HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy` →
  `VerifiedAndReputablePolicyState = 1` (**Smart App Control LIGADO**)
- Log `Microsoft-Windows-CodeIntegrity/Operational` mostra eventos
  **3077** + **3118** (`Smart App Control Block`)

### O diagnóstico que destrava

Testando componente por componente, fica claro que **o Whisper está inteiro**:

| Componente | Estado |
|---|---|
| `ctranslate2` (o motor que transcreve) | ✅ OK |
| `tokenizers`, `numpy`, `onnxruntime` (VAD) | ✅ OK |
| `av` (PyAV) — **só decodifica áudio** | ❌ costuma ser o único bloqueado |

O Smart App Control barra binário sem assinatura confiável, e o PyAV embute DLLs
de FFmpeg sem assinatura. Mas o PyAV **não transcreve nada** — ele só converte
mp4/mp3 em amostras.

### A solução

1. **Decodificar com o ffmpeg CLI** (`winget install Gyan.FFmpeg`) — o build do
   gyan.dev **passa** pelo Smart App Control. `_decode_audio_ffmpeg()` devolve um
   array numpy 16 kHz mono.
2. **Stub do `av`** — `faster_whisper/audio.py` faz `import av` no topo do módulo.
   Como `WhisperModel.transcribe()` aceita numpy array e nesse caso **nunca chama**
   `decode_audio()`, um módulo vazio em `sys.modules` basta pro import passar.

Resultado: PyAV fora do caminho, Smart App Control intacto, Whisper rodando.

> ⚠️ **Nunca desligar o Smart App Control.** É porta de mão única — o Windows 11
> não deixa religar sem reinstalação limpa. Não é preciso, e não vale o risco.

### Device: CPU por padrão

`device="auto"` do CTranslate2 escolhe CUDA assim que vê uma placa NVIDIA e
**pode morrer no meio da transcrição** (`Library cublas64_12.dll is not found`)
se as libs CUDA não estiverem lá.

Default é **CPU/int8** — confiável em qualquer máquina. Pra tentar a GPU:

```
uv pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
set WHISPER_DEVICE=cuda
```

Em GPUs mais antigas (arquitetura Pascal ou anterior) o ganho é modesto —
float16 não é bem suportado e int8 exige compute capability ≥ 6.1. Numa GPU
recente (Turing ou mais nova) o ganho tende a ser maior. Não é prioridade se
CPU já atende.

### Nomes próprios: sistema de vocabulário automático

O Whisper destrói nome próprio que nunca viu. Duas camadas resolvem, e **as duas
são automáticas** — ninguém precisa lembrar de passar nada:

**Camada 1 — `vocabulario/nomes.txt` → `initial_prompt`.**
Vira uma frase entregue ao modelo antes da transcrição, enviesando a
decodificação. Aplicado sozinho quando `initial_prompt` não é passado.
⚠️ O Whisper lê só ~224 tokens de prompt e, ao estourar, **corta o começo e
mantém o fim** — lista curta, o que mais importa no fim.

**Camada 2 — `vocabulario/correcoes.txt` → busca/substituição.**
Regras `errado => certo`, case-insensitive, com fronteira de palavra, aplicadas
ao texto e ao SRT. É a garantia determinística: o prompt *enviesa*, isto
*conserta*.

> ⚠️ **Legenda diz o que foi FALADO.** Corrigir grafia/reconhecimento: sim.
> Inserir palavra que ninguém disse: não. Edite `vocabulario/nomes.txt` e
> `vocabulario/correcoes.txt` com os nomes/termos do SEU conteúdo — os dois
> arquivos já vêm com exemplos e a explicação de como preencher.

**Por que a camada 2 é indispensável** — cada tamanho de modelo do Whisper erra
nomes desconhecidos de um jeito DIFERENTE (não existe um erro único e fixo pra
corrigir). Por isso as regras de `correcoes.txt` corrigem por **componente**
do nome (ex.: cada pedaço errado separadamente), não por combinação inteira —
isso cobre mais variações e continua valendo se você trocar de modelo.

**Armadilha a saber:** mexer no `initial_prompt` muda a decodificação inteira e
portanto **muda os erros** — uma correção que funcionava pode parar de casar
depois de você editar `nomes.txt`. Reveja as duas camadas juntas.

### Duas classes de erro, dois consertos diferentes

`correcoes.txt` já vem dividido nessas classes, e a distinção importa (leia os
comentários dentro do arquivo pra entender o exemplo completo em português):

| Classe | Exemplo | Conserto | Por quê |
|---|---|---|---|
| **A — nome próprio** | grafia errada de um nome | busca/substituição ✅ | a forma errada nunca é fala intencional |
| **B — colisão fonética** | duas frases que soam igual | **modelo maior** ⚠️ | a forma "errada" pode ser fala legítima |

**Classe B merece atenção especial:** às vezes o modelo não erra de ouvido —
ele acerta o som e erra ONDE cortar a palavra, porque duas frases diferentes
soam foneticamente idênticas na fala corrida. Busca/substituição é cega a
contexto, então uma regra de Classe B pode corromper uma fala legítima que
soa igual. Nesses casos o conserto certo é trocar pra um modelo maior (o
modelo de linguagem dele desambigua pelo contexto), não empilhar regra de
texto. Exemplo completo (com a explicação fonética) dentro de
`vocabulario/correcoes.txt`.

### Benchmark de modelos (medido em CPU/int8, sua máquina pode variar)

Áudio de referência de ~9min38s (578s):

| Modelo | Tempo aproximado | Velocidade | Qualidade |
|---|---|---|---|
| `base` | mais rápido | ~14× tempo real | mais erros de vocabulário/vício de linguagem |
| `small` | intermediário | ~5× tempo real | acerta mais nomes, ainda erra colisões fonéticas |
| `medium` | mais lento | ~1,7× tempo real | melhor equilíbrio texto/pontuação |

Use `small` pra rascunho rápido, `large`/`large-v3` se precisar do máximo
(mais lento que tempo real na CPU). Configure o padrão em `.mcp.json` via
`WHISPER_MODEL`.

Sempre passar `language="pt"` (ou o idioma do seu conteúdo) — evita o modelo
errar o idioma.

---

## 5. Como registrar no Claude Code

1. Copie `.mcp.json.exemplo` para `.mcp.json` na raiz deste repositório.
2. Edite os caminhos pra sua máquina:
   - `command`: caminho do `uv.exe` (ache com `where uv` no PowerShell).
   - `args` → `--directory`: caminho absoluto onde você clonou este repositório.
   - `RESOLVE_SCRIPT_LIB` / `RESOLVE_SCRIPT_API` / `PYTHONPATH`: normalmente já
     estão certos pra uma instalação padrão do Resolve no Windows — só mude se
     você instalou em outro lugar.
3. Abrindo o Claude Code nesta pasta, ele sobe o servidor sozinho.

Os tools de controle do Resolve vão responder com erro de conexão até existir o
**Studio** — isso é esperado, não é defeito da instalação.

Antes de usar: Resolve **aberto** com um projeto carregado. Com o Studio, ainda
falta ligar em `Preferences > System > General > External scripting using = Local`
(a opção passa a aparecer).
