---
name: reels-estrategista
description: O ESTRATEGISTA de retenção do kit de vídeo — analisa um vídeo bruto de conteúdo (Reels/Shorts/TikTok) e DECIDE o tratamento de edição pra prender a audiência, aplicando ciência de atenção (hook nos primeiros segundos, variação de ritmo, onde cortar), e só então orquestra as ferramentas mecânicas do kit na ordem certa. Use quando você quiser a CABEÇA da edição, não só a mão: "edita esse reels pra prender", "como eu edito esse vídeo pra segurar a audiência", "otimiza esse vídeo pra retenção", "analisa esse vídeo e me diz onde cortar", "prepara esse reels do jeito certo", "esse vídeo tá perdendo gente, arruma", "monta a estratégia de edição desse conteúdo". Também quando você entregar um vídeo bruto de conteúdo pedindo a MELHOR edição, sem especificar as etapas — esta skill decide quais aplicar. NÃO é pra uma etapa isolada já decidida (só legenda → legenda-video; só cor → colorir-video; só tirar pausa → cortar-silencio); esta entra quando a DECISÃO de o que fazer ainda não foi tomada.
---

# Reels Estrategista — a cabeça que decide como editar pra prender

Esta skill é a **camada estratégica** do kit de edição de vídeo (ver [`COMO_USAR.md`](../../COMO_USAR.md)). O kit sabe *executar* — cortar, colorir, legendar. O que faltava era **decidir**: onde está o gancho, onde cortar pra manter o ritmo, se precisa de b-roll, qual estilo casa com o conteúdo. É isso que esta skill faz — e depois delega a execução pras skills mecânicas.

O *porquê* de cada decisão vem do [Guia de Retenção](../../referencias/GUIA_RETENCAO.md) — os princípios acionáveis (hook, variação, ritmo, cortes) com o peso de evidência de cada um (o que é ciência dura vs. prática de mercado vs. ofício de editor). **É a fonte única dos princípios** — se um número mudar, muda lá, não aqui. Esta skill **consulta** o guia, não o recria.

## ⛔ DIRETRIZ-PRIMÁRIA (a regra-rainha, acima de todas)

> **Nenhuma edição por reflexo, e nada de prender por prender.** Todo corte, efeito, legenda e escolha de ritmo existe por uma **razão de retenção nomeável** — se você não sabe dizer por que aquele corte segura a atenção, não faça. E o que você prende, prende pra **entregar valor**: as mesmas alavancas que retêm são as que viciam (a ciência mostra isso sem meias-palavras), então o conteúdo que você está ajudando a prender tem que valer a atenção da pessoa — prende pra entregar algo útil, nunca pra sequestrar a atenção como fim. Ritmo sem razão vira ruído; retenção sem valor vira o mal que a própria pesquisa denuncia.

## O que a pessoa faz (mínimo) × o que o agente executa (todo o resto)

Quem usa só precisa **apontar o vídeo** e dizer o objetivo ("prende mais", "tá perdendo gente aqui"). Todo o diagnóstico, a decisão e a orquestração são do agente. A pessoa revê o **Plano de Retenção** (readout abaixo) antes de executar — e manda mudar o que quiser.

## O LOOP — ASSISTIR → DIAGNOSTICAR → PLANEJAR → (readout) → EXECUTAR → CONFERIR

Nomeado de propósito: é um ciclo, não uma lista solta. Nada termina sem conferir o resultado.

### 1. ASSISTIR (nunca decidir sobre o que não viu)
- `ffprobe` no arquivo: duração, resolução, se já é vertical (9:16), se tem áudio, se é 4K/longo (avisa que reencode demora).
- **Olhar o conteúdo de verdade**, não só os metadados: transcrever a fala (o `transcrever_palavras.py` do kit gera o `.palavras.json`) pra saber *o que* é dito e *quando*; extrair 3-5 frames ao longo do vídeo com ffmpeg e olhar com a Read tool. Sem isso, o diagnóstico é chute — e a diretriz-primária proíbe chute.

### 2. DIAGNOSTICAR (o vídeo contra os princípios de retenção)
Ler o [Guia de Retenção](../../referencias/GUIA_RETENCAO.md) e passar o vídeo por ele. Perguntas-guia:
- **Hook:** o primeiro 1-2s já prende (movimento/tensão/promessa), ou começa com arranque morto / "oi pessoal" / respiro? Onde no vídeo está o momento mais forte — dá pra puxá-lo pro começo?
- **Ritmo/variação:** há trechos parados (mesmo enquadramento, fala longa sem corte) onde a atenção cai? Onde o visual fica >3s sem mudar?
- **Tempos mortos:** há pausas/silêncios que arrastam?
- **Legibilidade sonora e visual:** áudio limpo e equilibrado? Precisa de legenda (quase sempre sim, pra consumo mudo)? Qual estilo casa com o tom (sério → `bloco`; punch/energia → `palavra`/`pop`)?
- **Formato:** está vertical? Se horizontal, precisa reframe 9:16.
- **Cor:** o look serve ao conteúdo, ou está cru/apagado?
- **Responsabilidade:** o conteúdo entrega valor real a quem parar pra ver? (A diretriz-primária.)

### 3. PLANEJAR (escada de decisão → etapas, na ordem-lei)
Traduzir o diagnóstico em etapas concretas. A **ordem é lei** (herdada do kit, ver `COMO_USAR.md`): `áudio → cor → cortar silêncio → reframe 9:16 → legenda`. A legenda é sempre a última porque é casada com o tempo da fala.

Escada de decisão (primeiro sinal presente → inclui a etapa; use julgamento, não é dogma):

| Sinal no diagnóstico | Etapa | Skill / script |
|---|---|---|
| Áudio de um lado só, ruído, volume irregular | tratar áudio | [tratar-audio](../tratar-audio/SKILL.md) · `60_audio.py` |
| Cor crua/apagada, ou tom pede um look | colorir | [colorir-video](../colorir-video/SKILL.md) · `70_cor.py` |
| Pausas/silêncios que arrastam | cortar silêncio | [cortar-silencio](../cortar-silencio/SKILL.md) · `50_cortar_silencio_externo.py` |
| Vídeo horizontal (não 9:16) | reframe vertical | `40_reframe_vertical.py` |
| Consumo mudo / sempre, salvo pedido contrário | legenda | [legenda-video](../legenda-video/SKILL.md) · `30_legenda_reels.py` |
| Gancho fraco / momento forte enterrado no meio | **recomendar reordenar** (o kit não corta-e-cola cena; sinalizar pra decisão humana) | — |
| Trecho parado longo pede corte visual / b-roll | **recomendar b-roll** | — |

As duas últimas linhas são **recomendações**, não execução automática: o kit atual não faz reordenação de cena nem inserção de b-roll sozinho, e forçar isso seria prometer o que a ferramenta não entrega. Sinalize com timestamp e razão, pra a pessoa decidir.

### 4. READOUT — o Plano de Retenção (imprimir SEMPRE antes de executar)
Automação com transparência: a pessoa vê a estratégia e sobrepõe o que quiser **antes** de qualquer reencode. Formato:

```
━━━ PLANO DE RETENÇÃO — <nome do vídeo> ━━━
Diagnóstico: <duração, formato, o que prende e o que perde — 2-3 linhas>
Hook: <onde está o momento forte / se o começo prende ou não>
Etapas (ordem-lei):
  1. <etapa> — porque <razão de retenção>
  2. ...
Recomendações (não executo sozinho): <reordenar / b-roll, com timestamp e razão>
Valor: <o conteúdo entrega algo a quem parar? — ok / ressalva>
→ Executo assim? Diga "muda X" pra ajustar, ou "só o diagnóstico" pra parar aqui.
```

Se a pessoa pediu só a análise ("me diz como editar"), **parar aqui** — o readout já é a entrega.

### 5. EXECUTAR (delegar às mecânicas, encadeando)
Rodar as etapas na ordem do plano, cada uma consumindo a saída da anterior (o `- AUDIO.mp4` entra na cor, e assim por diante). Cada script cospe arquivo novo — **o original nunca é tocado**. Avisar antes das etapas que reencodam (cor, corte, reframe, legenda) se o vídeo for 4K/longo. Os scripts ficam em `davinci-resolve-mcp/scripts_resolve/` e rodam com o venv de lá:

```
cd davinci-resolve-mcp
.venv\Scripts\python.exe scripts_resolve\<script>.py "C:\caminho\video.mp4" <opções>
```

### 6. CONFERIR (não entregar no escuro)
Depois de cada etapa visual (cor, reframe, legenda), extrair um frame e **olhar com a Read tool** — a diretriz-primária vale até o fim: não afirmar qualidade que não vi. Entregar com o caminho do final, o resumo do que foi feito e onde ficaram os intermediários (podem ser apagados).

## Modos (a pessoa diz → a skill faz)

| Ela diz | A skill faz |
|---|---|
| "prepara/edita esse reels pra prender" | loop completo (1→6) |
| "me diz como editar / só o diagnóstico" | para no readout (1→4) |
| "edita, mas sem legenda" (ou qualquer etapa a menos/a mais) | ajusta o plano no passo 3, segue |

## Como saber que funcionou (passou/falhou)

1. **O readout saiu antes de qualquer reencode** e a pessoa teve chance de sobrepor — nunca executei no escuro.
2. **Toda etapa no plano tem uma razão de retenção nomeada** (não "apliquei cor" solto, e sim "cor quente porque o tom é acolhedor e o cru estava apagando o rosto"). Se não sei a razão, não entrou — é a diretriz-primária.
3. **A ordem-lei foi respeitada** (legenda por último; corte antes de reframe/legenda).
4. **Cada etapa visual foi conferida por frame** — nada de "deve ter ficado bom".
5. **A responsabilidade sobre o conteúdo foi considerada explicitamente** no readout, não subentendida.
6. **O original está intacto** e o final é um arquivo novo.

## Limites conhecidos (honestidade operacionalizada)

- **Não reordeno cena nem insiro b-roll sozinho** — o kit não faz isso; eu recomendo com timestamp, a pessoa executa. Prometer o contrário seria mentir sobre a ferramenta.
- **Retenção real só se mede publicando** — o diagnóstico é a melhor decisão *a priori* com base na ciência, não garantia de números. A prova é o vídeo no ar.
- **Números de retenção "de blog" não valem** — só uso o que o [Guia de Retenção](../../referencias/GUIA_RETENCAO.md) marca como ciência dura (🟢); o resto é orientação, não fato.
</content>
