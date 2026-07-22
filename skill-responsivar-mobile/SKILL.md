---
name: responsivar-mobile
description: Pega um código/arquivo HTML e o deixa com responsividade perfeita em telas de celular — 5" e 5.5" (foco principal) e 6"+ — mexendo SÓ em CSS dentro de @media (max-width), sem tocar no layout desktop nem reestruturar o HTML. Roda um loop verificado num browser real que mede o overflow horizontal por scrollWidth em 5 larguras e só dá "pronto" quando zera em todas. Use SEMPRE que alguém disser "deixa esse HTML responsivo", "arruma o mobile dessa página", "tá vazando a tela no celular", "não cabe no celular", "responsividade mobile", "adapta pro celular", "conserta a responsividade", ou apontar um arquivo .html / uma página que quebra no celular pedindo pra ajustar. NÃO use pra redesenhar o visual/estética nem pra criar página do zero — esta skill só CONSERTA o encaixe no mobile, preservando o desktop.
---

# Responsivar Mobile — apertar até caber, sem quebrar o desktop

Deixar um HTML caber perfeito no celular é um problema **medível**, não de gosto: ou o conteúdo vaza a tela na horizontal, ou não vaza. Fazer isso "no olho" por screenshot erra — screenshot headless engana; a verdade é a **medida** `scrollWidth vs innerWidth` (é por isso que esta skill roda num browser real). O trabalho aqui é fechar essa medida em todas as larguras de celular, mexendo o mínimo possível.

## ⭐ DIRETRIZ-PRIMÁRIA (a regra-rainha, acima de tudo)

**Todo CSS que eu adicionar mora DENTRO de um `@media (max-width: ...)`. O layout desktop atual é intocável.** Se um conserto precisaria mudar como a página se vê no desktop, ele está errado — existe sempre uma forma de resolver só no mobile. E **não reestruturo o HTML** (não movo, agrupo nem removo elementos): só CSS. Isso torna a skill segura, reversível (é só apagar o bloco `@media`) e impossível de estragar o que já funciona.

> Se em algum caso raro for **impossível** caber só com CSS (ex.: uma tabela de 12 colunas de números que não pode virar bloco), **pare e avise a pessoa** qual é o elemento e por quê — não reestruture por conta própria.

## As 5 larguras de teste (fonte única — ajustar SÓ aqui)

"5 pol / 5.5 pol / 6+" é o tamanho físico da tela; o CSS enxerga a **largura em px lógicos**. O mapa real, e por que cada uma:

| px CSS | Aparelho / polegada | Por que está na lista |
|---|---|---|
| **320** | iPhone SE, Android básico (5") | O caso **mais apertado** que existe hoje. Cabe aqui → cabe em tudo. |
| **360** | Android comum 5"/5.5" | A largura de celular mais frequente no mundo. |
| **375** | iPhone 6/7/8/SE2 (5.5") | **O foco principal.** |
| **414** | iPhone Plus/XR/11 (6"+) | Fronteira dos grandes. |
| **430** | iPhone Pro Max (6.7") | O maior comum — pega problemas que só aparecem em tela larga de celular. |

Essas 5 são o padrão do motor. Trocou o parque de aparelhos-alvo? Muda-se **só esta tabela** e a linha de comando (`--larguras ...`).

## O motor de medição (não reinventar)

Quem mede e aponta o culpado é o script incluído nesta skill — Chrome headless real que mede `scrollWidth` e **lista os elementos que vazam** (tag, classe, right/left):

```bash
node scripts/verificar_responsivo.js <alvo>
```

- `<alvo>` = caminho do `.html` local **ou** URL (`https://...` / `http://localhost:PORTA` com o app rodando).
- Larguras padrão já são as 5 de celular; pra mudar: `--larguras 320,375,430`.
- **Exit 0 = passou** (0 overflow em todas as larguras) · **1 = reprovou** (imprime os culpados) · 2 = erro de ambiente.
- É esse exit code que fecha o loop desta skill. Não existe "responsivo no olho".
- Dependência (instalar uma vez): `npm i -D playwright && npx playwright install chromium` — ver `COMO_USAR.md`.

## O loop: MEDIR → CULPADO → CORRIGIR → PROVAR

O coração da skill é um ciclo. Ele **não termina** enquanto o motor não der exit 0.

**0. Achar o arquivo certo e travar o pré-requisito.**
   - Editar a **fonte** do HTML (se a página é gerada por um servidor/template, é lá que se edita — nunca um HTML gerado/temporário).
   - Antes de qualquer coisa, garantir os **dois pré-requisitos sem os quais nada de mobile funciona**:
     1. `<meta name="viewport" content="width=device-width, initial-scale=1">` no `<head>` — sem isso o celular finge ser 980px e "encolhe" a página (falso responsivo, texto minúsculo). **Esta é a única coisa que fica fora do `@media`** — é uma tag no `<head>`, não muda o desktop em nada, só liga o comportamento mobile.
     2. `*, *::before, *::after { box-sizing: border-box; }` — sem isso, `padding`/`border` **somam** à largura e estouram a tela mesmo com `width:100%`. Vai **dentro do `@media`** (não global): numa página feita sem border-box, aplicá-lo globalmente encolheria elementos no desktop — e o desktop é intocável.

**1. MEDIR.** Rodar o motor. Exit 0 já → pular pro passo 4 (a página já é responsiva; confirmar e reportar). Exit 1 → ler a lista de culpados.

**2. CULPADO.** Para cada elemento que o motor listou, identificar a **causa** do vazamento (a tabela abaixo cobre ~todos os casos). Corrigir a causa, não o sintoma — largar um `overflow-x:hidden` no `body` **esconde** o vazamento mas mantém o layout quebrado (conteúdo cortado). Isso é proibido como conserto; `overflow-x` só é legítimo no wrapper de um elemento que ROLA de propósito (tabela, bloco de código).

**3. CORRIGIR.** Adicionar as regras num único bloco `@media` no fim do CSS (ver "Onde escrever"). Voltar ao passo 1. Repetir até exit 0.

**4. PROVAR e reportar (fecha o ciclo).**
   - Motor deu exit 0 nas 5 larguras.
   - Rodar a **checagem de legibilidade** (complemento, não substitui a medida): inputs/selects com `font-size ≥ 16px` no mobile (abaixo disso o iOS dá zoom automático e desloca a tela); alvos de toque (botões, links) confortáveis. Ajustar dentro do mesmo `@media`.
   - Salvar. Se estiver sob controle de versão, commitar (rede de segurança — dá pra reverter o bloco inteiro).
   - Imprimir o **readout final** (modelo abaixo).

## Tabela causa → conserto (o miolo — quase todo overflow é um destes)

Todo conserto vai dentro do `@media (max-width: ...)`.

| O que o motor aponta / a causa | Conserto em CSS |
|---|---|
| Elemento com **largura fixa em px** maior que a tela (`width: 500px`) | `width: auto; max-width: 100%;` |
| **Imagem / vídeo / iframe** sem limite | `img, video, iframe { max-width: 100%; height: auto; }` |
| **Flex** numa linha só que não cabe (`display:flex` sem wrap) | `flex-wrap: wrap;` nos containers |
| **Item de flex/grid que não encolhe** (texto longo empurra) | no item: `min-width: 0;` (o padrão `min-width:auto` impede encolher — causa nº 1 escondida) |
| **Grid de N colunas fixas** | no mobile: `grid-template-columns: 1fr;` (ou `repeat(auto-fit, minmax(0, 1fr))`) |
| **Texto/URL/palavra longa** sem quebra estoura | `overflow-wrap: break-word; word-break: break-word;` |
| **`white-space: nowrap`** forçando linha única | no mobile: `white-space: normal;` |
| **Tabela larga** de dados que não vira bloco | envolver a tabela e no wrapper: `overflow-x: auto;` (rolagem intencional — legítimo) |
| **`<pre>` / bloco de código** | `pre { overflow-x: auto; }` (ou `white-space: pre-wrap;`) |
| **`100vw`** (inclui a barra de rolagem → alguns px a mais) | trocar por `100%` |
| **`position: absolute/fixed`** saindo pela direita | ajustar `right`/`left`/`max-width` no mobile |
| **Margens/paddings grandes em px** | reduzir no mobile (`padding: 12px` no lugar de `48px`) |

## Onde escrever o CSS (não espalhar)

Um **único bloco no fim do CSS existente**, comentado, pra ser óbvio e reversível:

```css
/* === responsivar-mobile: ajustes só de celular (não afeta desktop) === */
@media (max-width: 480px) {
  /* consertos aqui */
}
```

`480px` cobre todos os celulares-alvo (o maior é 430) sem tocar em tablet/desktop. Se um problema só aparecer nos maiores (414/430) e não nos menores, pode-se usar um segundo `@media (max-width: 640px)` — mas o padrão é um bloco só. Nunca editar as regras desktop existentes; se uma regra desktop é a causa, **sobrescreve-se** dentro do `@media`, não se altera a original.

## Readout final (sempre imprimir — transparência)

```
📱 responsivar-mobile — <arquivo>
Larguras testadas: 320 · 360 · 375 · 414 · 430  → overflow: 0/0/0/0/0 ✅
Consertos aplicados (N): <lista curta: "imagens do hero → max-width:100%", "grid de cards → 1 coluna", ...>
Legibilidade: inputs ≥16px ✔ · toque confortável ✔
Desktop: intocado (tudo dentro de @media max-width:480px)
Quer que eu ajuste algum ponto específico? (a skill mediu, não julgou o gosto)
```

## Como saber que funcionou (passou/falhou)

- O motor imprimiu **exit 0** nas 5 larguras (0 overflow em todas). Esse é o critério duro.
- **Nenhuma** regra CSS nova ficou fora de `@media` — a única mudança fora dele é a viewport meta no `<head>` (que não é CSS e não afeta o desktop). Dá pra conferir por leitura: todo o diff de CSS está dentro do bloco. Se editei uma regra desktop existente, **falhei a diretriz-primária**.
- O conserto não foi `overflow-x:hidden` no body pra **esconder** o vazamento — o conteúdo cabe de verdade (some a barra horizontal E nada de conteúdo foi cortado).
- Página propositalmente quebrada (ver `exemplo/quebrado.html`) entra reprovando e sai passando; se um HTML já responsivo "precisou" de conserto, desconfie — o motor ou o alvo está errado.
