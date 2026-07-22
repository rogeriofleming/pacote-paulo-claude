# Como instalar e usar o Responsivar Mobile

## O que é

Uma skill que pega um **arquivo HTML** e o deixa **responsivo perfeito no celular** — telas
de 5", 5.5" (o foco) e 6"+ — mexendo **só em CSS**, dentro de `@media (max-width)`, **sem
tocar no layout desktop** e sem reestruturar o HTML.

O pulo do gato: ela não faz "no olho". Ela roda um **loop verificado num browser real** que
**mede** o overflow horizontal (`scrollWidth`) em 5 larguras de celular e **aponta o elemento
exato que está vazando a tela**. Só dá "pronto" quando zera em todas — não existe "responsivo
mais ou menos".

## Instalação

**1. Copie a pasta da skill** pra `.claude/skills/responsivar-mobile/` na raiz do seu projeto:
```
.claude/skills/responsivar-mobile/SKILL.md
.claude/skills/responsivar-mobile/scripts/verificar_responsivo.js
.claude/skills/responsivar-mobile/exemplo/quebrado.html
```
O Claude Code carrega a skill automaticamente.

**2. Instale o motor de medição** (uma vez só, na raiz do projeto):
```bash
npm i -D playwright
npx playwright install chromium
```
Isso baixa um Chrome próprio pro teste (não depende do navegador do seu sistema). Se você já
tem `playwright-core` e um Chrome/Edge instalado, o script também usa esse — mas o jeito acima
é o mais simples e funciona em Windows, Mac e Linux.

## Como acionar

Peça direto ao Claude:
> *"deixa essa página responsiva no celular: caminho/pagina.html"*
> *"tá vazando a tela no celular, arruma o mobile"*
> *"responsividade mobile desse HTML"*

O Claude vai: medir → ver o que vaza → consertar só no CSS mobile → medir de novo, até fechar.

## Rodar o medidor na mão (opcional)

Você não precisa — a skill roda sozinha —, mas dá pra chamar o motor direto:
```bash
node .claude/skills/responsivar-mobile/scripts/verificar_responsivo.js caminho/pagina.html
```
- Sai com **exit 0** se está tudo certo, **1** se algo vaza (e lista os culpados).
- Larguras padrão: 320, 360, 375, 414, 430. Pra mudar: `--larguras 320,375,430`.
- Funciona com URL também: `... verificar_responsivo.js https://seusite.com`

## Teste rápido (prova que funciona)

Tem um arquivo `exemplo/quebrado.html` de propósito cheio de problemas de mobile. Rode:
```bash
node .claude/skills/responsivar-mobile/scripts/verificar_responsivo.js .claude/skills/responsivar-mobile/exemplo/quebrado.html
```
Ele vai **reprovar** e listar os elementos que vazam. Aí peça ao Claude *"deixa esse
quebrado.html responsivo"* e rode de novo — deve passar (exit 0). É o loop inteiro em ação.

## O que ela NÃO faz

- **Não deixa bonito/premium** — ela faz *caber*, não faz *elegante*. Estética é outra tarefa.
- **Não cria página do zero.**
- **Não mexe no desktop** nem reestrutura o HTML (por design). Se um layout for impossível de
  salvar só com CSS, ela **para e te avisa** qual elemento é o problema, em vez de bagunçar.
