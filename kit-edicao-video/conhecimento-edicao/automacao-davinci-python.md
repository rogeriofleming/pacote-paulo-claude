# Relatório — Automação Python no DaVinci Resolve (Free) para edição de Reels/Shorts/TikTok

**Pesquisa** (buscas com verificação cruzada, 2026)

---

## Sumário executivo

A distinção Free/Studio no scripting do Resolve opera por **dois mecanismos independentes e compatíveis**: (1) bloqueio de **conexão** — scripting *externo* (processo fora do Resolve, conectando via `fusionscript.dll`) exige Studio, enquanto scripting *interno* (rodado por dentro do processo, via menu `Workspace > Scripts`) funciona no Free — o que também se confirma em testes práticos; e (2) bloqueio por **função específica**, em que chamadas marcadas Studio-only retornam status `False`/erro mesmo dentro de uma conexão já estabelecida, em vez de travar o script inteiro. Um exemplo concreto e confirmado do segundo mecanismo é o `UIManager`: a partir do v19.1 ele foi **removido por inteiro** do Free (mudança de política confirmada pela própria Blackmagic no fórum oficial), o que mostra que os limites do Free **pioraram com o tempo** — não é uma lista estática de exceções. A pesquisa **não conseguiu fechar a lacuna central** pedida: uma tabela oficial recurso-a-recurso (Smart Reframe, Magic Mask, Scene Cut Detection, Create Subtitles from Audio, Stabilization, Voice Isolation, `AppendToTimeline`, render, LUT/nós de cor, EDL, marcadores, transições) discriminando Free-interno vs Studio simplesmente não existe publicada — nem na doc oficial nem no fórum — e permanece um gap real. Para o objetivo prático (produzir Reels/Shorts em volume), o padrão de mercado 2026 confirmado em múltiplas fontes independentes é processar **tudo fora do Resolve** (corte de silêncio, transcrição Whisper, reframe vertical via visão computacional, legenda queimada) e usar o Resolve só na ponta, para grading/timeline final/entrega — nenhuma fonte encontrada descreve produção em escala via a API interna do Resolve.

---

## Achados confirmados

### 1. O bloqueio Free/Studio é de CONEXÃO, não um bloco monolítico de API — confiança: **alta**
Scripting externo (processo fora do Resolve) exige Studio; scripting interno (via `Workspace > Scripts`, rodando dentro do processo do Resolve) **funciona no Free**, com acesso aos objetos `resolve`/`fusion`/`bmd`. Isso se confirma em testes práticos e foi corroborado contra uma fonte que afirmava o contrário — o claim genérico "a versão free não expõe a API de scripting" foi checado e **refutado**: fórum oficial da Blackmagic e outras fontes (dev.to, wildlion.media) confirmam a distinção externo × interno.
- Fontes: [Blackmagic Forum — "Scripting in the free version?"](https://forum.blackmagicdesign.com/viewtopic.php?f=21&t=113252) _(verificado adversarialmente)_.

### 2. Dentro de uma conexão já estabelecida, o bloqueio é por FUNÇÃO específica (retorno False/erro), não geral — confiança: **alta**
A doc oficial da Blackmagic (README.txt da API, replicado identicamente em 3 mirrors independentes — extremraym.com, deric.github.io, wiki.dvresolve.com) declara: chamadas de API podem retornar com status `False` (ou erro apropriado) quando a função referenciada é exclusiva do Studio e o Resolve rodando é o Free. Ou seja, o mecanismo é granular — falha pontual, não trava o processo inteiro.
- _(verificado adversarialmente; ver síntese acima.)_
- **Importante:** isso NÃO contradiz o achado #1 (bloqueio de conexão externa é binário) — são dois mecanismos de restrição diferentes e compatíveis entre si.

### 3. UIManager foi removido do Free inteiro a partir do v19.1 (não é "função isolada marcada") — confiança: **alta**
Sem aviso no changelog, a Blackmagic removeu o `UIManager` (construção de UI para scripts, usado por ferramentas como o Reactor) da versão Free a partir do v19.1. Corroborado por resposta oficial da própria Blackmagic no fórum: *"scripting through any UI has been the domain of the Studio version — this includes UIManager based scripts and Workflow Integrations"*. Este é um dado importante para calibrar expectativa: os limites do Free **pioraram com versões mais recentes**, não são fixos desde sempre.
- Fontes: [extremraym.com/cloud/resolve-scripting-doc](https://extremraym.com/cloud/resolve-scripting-doc/); [Blackmagic Forum — "Features quietly removed from Resolve Free?"](https://forum.blackmagicdesign.com/viewtopic.php?f=21&t=216545) _(verificado adversarialmente)_.

### 4. Env vars de scripting externo existem para o script achar a localização da API — confiança: **alta**
Confirma o mecanismo básico do setup: `RESOLVE_SCRIPT_API`, `RESOLVE_SCRIPT_LIB` e `PYTHONPATH` existem porque um script rodando de pasta externa precisa "saber onde está" a API/DLL — replicado identicamente em múltiplos mirrors (GitHub diop/davinci-resolve-api, gist mhadifilms, extremraym.com).
- Valores padrão Windows (das buscas, ver seção Ambiente Windows abaixo).
- _(verificado adversarialmente.)_

### 5. Causa raiz de um erro clássico de import no Windows: `%VAR%` não expande dentro de outra env var — confiança: **média-alta**
Um relato técnico de primeira mão (blog, com evidência reproduzida via `sys.path`) mostra que `os.path.expandvars()`/o encadeamento do Windows não expande `%RESOLVE_SCRIPT_API%` quando ela está sendo usada dentro de outra variável (`PYTHONPATH`), resultando em caminho literal inválido (`C:\Users\MUser\%RESOLVE_SCRIPT_API%\Modules`). Solução prática: usar caminho absoluto completo em vez da env var aninhada.
- Fonte: blog.corrlabs.com _(verificado adversarialmente)_. (Fonte é blog pessoal, não documentação oficial — adequada só para este claim pontual.)

### 6. FFmpeg em pipelines de reframe automático entra só como etapa final de encode — confiança: **média** (confirmado em 1 projeto exemplo)
No projeto `KazKozDev/auto-vertical-reframe` (reframe 9:16 com detecção de cena + rastreamento de sujeito), o ffmpeg só aparece no ÚLTIMO estágio (encode do MP4 final com encoder/CRF/bitrate configuráveis) — a detecção de cena é feita por PySceneDetect, e a detecção/rastreamento de sujeito por YOLOv11-seg + ByteTrack + MediaPipe. Isso confirma um padrão de arquitetura comum (visão computacional em Python + ffmpeg só para codificar a saída), mas é evidência de **um projeto**, não uma regra universal do ecossistema.
- Fonte: [github.com/KazKozDev/auto-vertical-reframe](https://github.com/KazKozDev/auto-vertical-reframe); vereditos `02.md` e `03.md`.

---

## Achados não fechados (gaps reais — não confundir com "provavelmente não")

### 7. Tabela recurso-a-recurso do Neural Engine (Smart Reframe, Magic Mask, Scene Cut Detection, Create Subtitles from Audio, Stabilization, Voice Isolation) — **NÃO ENCONTRADA**
As buscas dedicadas a isso (busca 2, com refinamento de query) não trouxeram nenhuma fonte — oficial ou de fórum — que discrimine, recurso por recurso, se essas features do Neural Engine são:
- (a) Studio-exclusivas como **feature de produto** (nem aparecem no menu do Free), ou
- (b) disponíveis no Free mas bloqueadas **só quando chamadas via script** (function-level, como o mecanismo do achado #2).

Isso é diferente de "confirmado que são Studio-only" — é um **gap de informação real**, não uma conclusão. A única forma prática de fechar isso é teste direto na sua instalação (chamar cada método via `Workspace > Scripts` e observar se retorna resultado ou `False`/erro), não mais busca documental — a própria busca 1 já apontou isso como "próximo passo mais promissor" e não foi possível avançar dentro do limite de 2 WebFetch.

### 8. `AppendToTimeline`, criação de timeline nova, render programático (`AddRenderJob`/`StartRendering`), `SetLUT`/nós de cor, EDL import/export, `AddMarker`, transições programáticas — sintaxe existe, restrição Free×Studio **não testada por método**
A API completa (nomes de método, assinaturas) está bem documentada em fontes não-oficiais abrangentes (gist X-Raym v21, deric.github.io, CommandPost/ResolveCafe) e há até discussão de bug real de `AddRenderJob()` no fórum oficial (evidência de uso prático — mas não prova se roda igual no Free). Nenhuma fonte confirma ou nega explicitamente se essas chamadas específicas funcionam via script interno no Free. Transições programáticas (cross dissolve etc.) não apareceram em nenhuma fonte pesquisada — gap total, sem indício em nenhuma direção.
- Fontes: gist X-Raym v21, deric.github.io, `forum.blackmagicdesign.com/viewtopic.php?f=12&t=210618` (confirma só que `SetLUT` usa index 1-based desde v16.2 — sintaxe, não permissão Free/Studio).

### 9. Um claim testado especificamente sobre isso foi REFUTADO por excesso de confiança — confiança da refutação: **alta**
A hipótese "scripts internos têm acesso pleno à API tanto no Free quanto no Studio, exceto funções explicitamente marcadas Studio-only" foi checada e refutada: a busca trouxe evidência específica contrária (inclusive o próprio caso do UIManager, que virou Studio-only por CATEGORIA INTEIRA em v19.1, não uma função isolada "marcada"). Ou seja, a moldura otimista de "quase tudo funciona, só umas exceções pontuais" não se sustenta — a realidade parece ter mais restrições e mais imprevisibilidade version-a-version do que isso.
- _(verificado adversarialmente.)_

---

## Tabela consolidada — recurso → Free/Studio → automatizável por Python → como

| Recurso | Free ou Studio | Automatizável por Python? | Via (interno/externo) | Confiança |
|---|---|---|---|---|
| Rodar script Python básico dentro do Resolve | Ambos | Sim | **Interno**, `Workspace > Scripts` | Alta (confirmado + validável na prática) |
| Scripting externo (processo fora do Resolve) | **Studio only** | Sim, no Studio | Externo, via `fusionscript.dll` + env vars | Alta (confirmado + validável na prática) |
| Objetos básicos (`resolve`, `fusion`, `bmd`, `ProjectManager`) dentro do processo | Ambos | Sim | Interno no Free | Alta |
| `UIManager` (construir GUI dentro de um script) | **Studio only desde v19.1** (removido do Free) | Não, no Free ≥19.1 | — | Alta (confirmado, inclusive resposta oficial Blackmagic) |
| `MediaPool.AppendToTimeline` / criar timeline nova via script interno no Free | **Não confirmado** | Presumido sim (é núcleo básico da API), mas sem confirmação direta | Interno (não testado nesta pesquisa) | Baixa — gap, próximo passo é teste prático |
| `AddRenderJob` / `StartRendering` (render programático) | Sintaxe documentada; restrição Free×Studio não testada | Presumido possível | — | Baixa |
| `SetLUT` / manipulação de nós de cor | Sintaxe documentada (index 1-based desde v16.2) | Restrição Free×Studio não testada | — | Baixa |
| EDL import/export, `AddMarker` | Sintaxe documentada na API geral | Restrição Free×Studio não testada | — | Baixa |
| Transições programáticas (cross dissolve etc.) | Nenhuma fonte encontrada | — | — | Não verificado — gap total |
| Smart Reframe / Magic Mask / Scene Cut Detection / Create Subtitles from Audio / Stabilization / Voice Isolation (Neural Engine) | **Não confirmado** se é Studio-exclusive como feature de produto vs bloqueio de API | — | — | Gap — nenhuma fonte oficial recurso-a-recurso |
| Reframe vertical 9:16 automatizado (fora do Resolve) | N/A | Sim, comprovado (projeto real) | **Externo total** — ffmpeg + PySceneDetect + YOLOv11 + ByteTrack + MediaPipe (ex.: KazKozDev/auto-vertical-reframe) | Alta (confirmado, mas é 1 projeto-exemplo, não regra do ecossistema) |
| Corte de silêncio/palavra | N/A | Sim | **Externo total** — ffmpeg + whisper | Alta (validável na prática) |
| Transcrição local (faster-whisper) | N/A | Sim | **Externo total**, sem precisar do Resolve nem de Studio | Alta (verificado localmente) |

---

## Pipeline recomendado para volume de Reels/Shorts/TikTok (2026)

Padrão consistente encontrado em múltiplas fontes independentes (KazKozDev/auto-vertical-reframe, mazsola2k/ai-video-editor, MindStudio, Forasoft — confiança **média**, é panorama de mercado/prática, não doc técnica de uma fonte única):

1. **Fora do Resolve, 100%:** detecção de silêncio/corte de palavra (ffmpeg + whisper), transcrição (faster-whisper local), reframe vertical 9:16 (visão computacional: PySceneDetect + YOLOv11/ByteTrack/MediaPipe), queima de legenda a partir de SRT, ajuste de ritmo. FFmpeg entra tipicamente só como etapa final de encode.
2. **Dentro do Resolve, mão humana ou script interno (não confirmado):** grading/cor, timeline final, entrega. Nenhuma fonte descreve uso da API interna do Resolve para essas etapas de produção em volume — o padrão de mercado parece **evitar** a API do Resolve para o trabalho pesado e reservá-lo só para o que só ele faz bem.
3. Um dado de ordem de grandeza (fonte de mercado, não testado): pipeline automatizado reduz edição de ~48h manuais para <45min.

---

## Ambiente Windows — variáveis e erros comuns

- **Env vars padrão (scripting externo, Windows):**
  - `RESOLVE_SCRIPT_API=%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\`
  - `RESOLVE_SCRIPT_LIB=C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll`
  - `PYTHONPATH=%PYTHONPATH%;%RESOLVE_SCRIPT_API%\Modules\`
- **Erro clássico:** `ModuleNotFoundError: No module named 'DaVinciResolveScript'` — ocorre quando as 3 variáveis não estão configuradas (script externo) OU, segundo um relato técnico específico, mesmo com env vars "configuradas" se o Windows não expandir `%RESOLVE_SCRIPT_API%` dentro de `PYTHONPATH` (usar caminho absoluto resolve).
- **Compatibilidade Python:** README cita mínimo 3.6, mas a faixa que funciona na prática é 3.10–3.12 (não verificado com fonte forte — inferência de blog/guia da comunidade). `fusionscript` é lib compilada atrelada a uma versão de Python; versões muito novas tendem a quebrar.
- **Diferenças version-a-version confirmadas:** v16.2+ node indexing 1-based; v19.1 removeu UIManager do Free (achado #3, confirmado). Diferenças adicionais citadas mas **não verificadas**: v18.1+ removeu exportação FCPXML 1.3-1.7; v20.3 adicionou `GetTimelineByName()`.
- Não foi encontrado (nem nesta nem na pesquisa anterior) um changelog consolidado version-a-version específico para scripting — as fontes tratam a config de ambiente como estável entre versões recentes, com a política Free/Studio (achado #3) sendo o fator que mudou.

---

## Ressalvas (o que é fraco ou pode estar desatualizado)

1. **Fontes majoritariamente secundárias** — mirrors/docs de comunidade (extremraym.com, deric.github.io, gists), não o texto bruto do README.txt oficial obtido diretamente por fetch (o limite de 2 WebFetch nesta pesquisa não permitiu puxar a fonte primária bruta para todos os claims). Onde houver conflito, a doc oficial/fórum oficial devem prevalecer sobre blog pessoal.
2. **KazKozDev/auto-vertical-reframe é 1 projeto-exemplo** — usado para confirmar um padrão de arquitetura (ffmpeg só no encode final), não prova que todo o ecossistema de reframe segue esse desenho.
3. **Um veredito (07) foi descartado por risco de alucinação de fonte** — a citação de apoio fornecida não foi confirmada como texto literal existente na página-fonte; tratado como refutado por segurança, não como "quase confirmado".
4. **A pergunta mais valiosa da pesquisa original (item 1 e 2 do pedido) permanece em aberto** — não é fraqueza de fonte, é ausência real de fonte publicada. Só teste prático na sua instalação fecha isso.

## Perguntas em aberto (para a próxima sessão/teste prático)

1. Chamar `MediaPool.AppendToTimeline`, `AddRenderJob`, `SetLUT`, `AddMarker` e export de EDL **diretamente via `Workspace > Scripts` na sua instalação (Resolve free)** e observar se retornam resultado normal ou `False`/erro — é o teste mais rápido para fechar o gap #7 e #8, mais confiável que qualquer busca adicional.
2. Testar se os botões/menus das features do Neural Engine (Smart Reframe, Magic Mask, Scene Cut Detection, Create Subtitles from Audio, Stabilization, Voice Isolation) aparecem no menu do Free desta instalação — isso já responde "feature de produto bloqueada" vs "só bloqueio de API" sem precisar de fonte externa.
3. Vale useful esforço documental adicional em buscas restritas por recurso único (ex.: `site:forum.blackmagicdesign.com "Smart Reframe" API free`), já que buscas compostas com muitos termos técnicos diluíram os resultados — mas o teste prático (#1 e #2 acima) é mais barato e definitivo.
4. Se o resultado do teste prático confirmar que `AppendToTimeline`/render funcionam no Free interno, o próximo passo lógico é decidir se vale a pena escrever esses scripts internos ou se o pipeline 100%-externo (achado da seção "Pipeline recomendado") já é suficiente para o volume de conteúdo desejado — essa decisão de engenharia ainda não foi tomada.
