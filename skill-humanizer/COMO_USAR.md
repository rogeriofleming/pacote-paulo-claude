# Como instalar e usar o Humanizer

## O que é

Uma skill que **tira a "cara de IA" de um texto** — deixa a escrita soar natural e
humana. Ela detecta e conserta 33 padrões típicos de texto gerado por LLM: símbolos
inflados, linguagem promocional, "regra de três", excesso de travessão, voz passiva,
frases de preenchimento, tom bajulador, conclusões genéricas, emoji decorativo, etc.

É baseada no guia [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
da Wikipedia. É uma skill de terceiro (MIT, © Siqi Chen — ver `LICENSE`); aqui vai
sem nenhuma alteração além deste guia em português.

> ⚠️ Os padrões e exemplos do `SKILL.md` estão em **inglês** (o guia-fonte é em inglês).
> A skill funciona para revisar texto em qualquer idioma, mas os exemplos de
> "antes/depois" são em inglês. Ela é ótima em texto em inglês; em português ela
> pega os padrões estruturais (voz passiva, regra de três, travessão, bajulação,
> preenchimento), que também aparecem no nosso idioma.

## Instalação

Copie a pasta pra `.claude/skills/humanizer/` na raiz do seu projeto:
```
.claude/skills/humanizer/SKILL.md
.claude/skills/humanizer/LICENSE
```
O Claude Code carrega a skill automaticamente.

## Como acionar

```
/humanizer

[cole seu texto aqui]
```

Ou peça direto: *"humaniza esse texto: ..."* / *"tira a cara de IA disso"*.

### Calibrar pra sua voz

Pra não virar um texto "limpo genérico", dê uma amostra do seu jeito de escrever:
```
/humanizer

Amostra da minha escrita (2-3 parágrafos meus):
[cole aqui]

Agora humaniza este texto:
[cole o texto de IA]
```
A skill analisa seu ritmo de frase, escolhas de palavra e manias, e aplica isso na
reescrita.

## Combina com

A skill de **Brevidade Inteligente** (neste mesmo repo): humanizer tira a cara de
robô, brevidade corta o excesso. Rodar as duas em sequência deixa o texto natural
**e** enxuto.
