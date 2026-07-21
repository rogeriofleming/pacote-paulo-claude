# Como instalar e usar o Find Skills

## O que é

Ajuda a **descobrir e instalar skills** do ecossistema aberto de agent skills (o "app
store" de skills do Claude Code, via `npx skills` e o site https://skills.sh/). Quando
você pede "tem uma skill pra X?" / "como eu faço Y?", ela busca, filtra por qualidade
(instalações, fonte confiável) e te mostra as opções com o comando de instalar.

## Instalação

Copie a pasta pra `.claude/skills/find-skills/` na raiz do seu projeto:
```
.claude/skills/find-skills/SKILL.md
```

## Como acionar

"acha uma skill pra X", "tem skill que faz Y?", "como eu faço Z com uma skill?".

## Cuidado (importante)

Uma skill é **código + instruções que rodam com as permissões do seu agente**. Antes de
instalar algo de terceiro, leia o `SKILL.md` e os scripts, e prefira fontes conhecidas
com contagem real de instalações. No Windows, se `npx skills add` criar um symlink que
não funciona, copie a skill pra uma pasta real em `.claude/skills/<nome>/`.
