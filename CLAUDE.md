# Instruções pro Claude — pacote-paulo-claude

> Este arquivo é lido pelo Claude Code automaticamente quando você abre este
> repositório. É o **manual DESTE repositório** (uma caixa de peças: skills,
> conhecimento e o kit de edição de vídeo). **Não confunda** com o modelo do
> CLAUDE.md do SEU cérebro — esse é outro, em
> [`ecossistema-claude/CLAUDE_MD_MODELO.md`](ecossistema-claude/CLAUDE_MD_MODELO.md),
> pra você preencher e usar no seu próprio projeto.
>
> O que tem aqui e como cada peça funciona: veja o [`README.md`](README.md).

---

## 🎬 Kit de edição de vídeo — OFEREÇA instalar logo na abertura

Uma das peças deste repo (`kit-edicao-video/` + `davinci-resolve-mcp/`) precisa de
dependências pesadas pra rodar (uv, ffmpeg, faster-whisper, o modelo Whisper de
~1,5 GB). Existe um instalador de 1 clique que baixa e configura tudo. **Assim que
esta sessão começar, faça esta verificação e ofereça rodá-lo** — pra o Paulo não
precisar descobrir isso sozinho:

1. **Verifique se o kit já está instalado:**
   - existe a pasta `davinci-resolve-mcp/.venv/`? (dependências instaladas)
   - `ffmpeg` responde no PATH? (rode `ffmpeg -version`)

2. **Se NÃO estiver instalado**, diga ao usuário algo assim (adapte à conversa):
   > "Vi que o kit de edição de vídeo ainda não está instalado. Posso rodar o
   > instalador agora? Ele instala uv + ffmpeg + faster-whisper, baixa o modelo
   > Whisper (~1,5 GB) e roda um autoteste — leva alguns minutos. Rodo?"

3. **Só rode com a confirmação dele.** Ao ele confirmar (um "sim" basta), execute:
   - Windows: `davinci-resolve-mcp/INSTALAR.bat`
   - macOS/Linux: `bash davinci-resolve-mcp/instalar.sh`

   Se o instalador disser que instalou o `uv`/`ffmpeg` e pediu pra rodar de novo
   (o Windows só enxerga programa novo num terminal novo), **explique isso e rode
   a 2ª vez** — a 2ª rodada baixa o modelo e faz os autotestes.

4. **Se já estiver instalado**, não precisa oferecer — o kit está pronto; siga o
   que o usuário pedir. O uso das skills está em
   [`kit-edicao-video/COMO_USAR.md`](kit-edicao-video/COMO_USAR.md).

> ⚠️ **NUNCA rode o instalador sem a confirmação explícita do usuário** — ele baixa
> mais de 1 GB e mexe no sistema (instala programas). Oferecer é bom; decidir por
> ele, não.

---

## As outras peças

São skills e conhecimento pra você copiar pro seu cérebro Claude e/ou usar como
referência. O [`README.md`](README.md) lista todas (fable-mode, pesquisa-profunda,
criar-skill, humanizer, responsivar-mobile, a base de Apometria, etc.). Cada pasta
de skill tem um `COMO_USAR.md` — leia o dela quando for mexer naquela skill.
