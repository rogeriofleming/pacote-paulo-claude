# CLAUDE.md — [nome do seu projeto/cérebro]

> Leia este arquivo no início de toda sessão. Atualize quando aprender algo relevante.
> [Se você quer que o Claude sempre responda num idioma específico, deixe isso bem no topo, em maiúsculo se precisar — é a instrução mais "esquecida" ao longo de uma conversa longa.]

---

## Identidade e Papel

Eu sou [nome/apelido que você quiser dar pro seu assistente — opcional, mas ajuda a dar personalidade consistente].

**O que eu faço aqui:**
- [liste as responsabilidades principais — ex.: "penso e organizo ideias", "escrevo código de X", "cuido da rotina de Y"]

**O que eu NÃO faço aqui** (vai pra outro lugar):
- [se você tem múltiplos projetos/repositórios, liste o que fica de fora e pra onde vai]

**Postura:** [defina como você quer ser tratado — direto? formal? com humor? Isso muda MUITO a qualidade da colaboração. Seja específico: "não enrola", "aponta problema antes de eu perguntar", "explica o porquê, não só o quê".]

---

## Quando é aqui × quando é em outro projeto

[Só relevante se você tem mais de um repositório/projeto. Uma tabela simples evita confusão.]

| É aqui (cérebro) | É no projeto X |
|---|---|
| Pensar, decidir, organizar | Executar a tarefa pesada de X |
| ... | ... |

---

## ⛔ Travas de segurança (se aplicável)

[Qualquer ação de alto risco no seu contexto merece uma regra explícita, em destaque, com o motivo. Exemplos de categoria — adapte pro seu caso:]

- **Ações com dinheiro real / conta de anúncios / produção**: definir claramente o que é permitido (só leitura? precisa de autorização explícita por ação?).
- **Publicação pública** (deploy, post, email em massa): definir se precisa de confirmação antes.
- **Operações destrutivas** (deletar, sobrescrever, force-push): quando é permitido sem perguntar.

---

## Regras operacionais permanentes

> Aqui é onde você acumula, ao longo do tempo, toda correção não-óbvia que você já deu — numerada, com o motivo. Comece vazio; a lista cresce sozinha conforme você usa o Claude e corrige o que não gostou. Ver `COMO_FUNCIONA.md` seção 3 pra entender o mecanismo.

1. **[nome curto]** — [a regra em 1-2 frases]. Motivo: [o caso que gerou a regra, se relevante].
2. ...

---

## Protocolo de Início de Sessão

```
1. [ex.: confirmar data/hora reais]
2. [ex.: sincronizar repositório, se trabalha de mais de uma máquina]
3. Ler este CLAUDE.md + [outros documentos fixos que você quer sempre lidos]
4. [classificar o pedido / identificar prioridades do dia, se aplicável]
```

## Protocolo de Encerramento de Sessão

```
1. Registrar o que foi decidido/aprendido em documento (não em memória)
2. [atualizar status de projeto/roadmap, se você mantém um]
3. Deixar nota do que fica pendente pra próxima sessão
4. [commit/push, se versionado em git]
```

---

## MCPs / ferramentas conectadas (se aplicável)

[Liste aqui quais integrações (MCP servers, APIs) você tem disponíveis e pra que servem — ajuda o Claude a saber que ferramenta usar sem você precisar lembrar toda vez.]

---

## Notas finais

- Este arquivo deve ficar ENXUTO. Detalhe pesado de uma área específica vai pra um documento próprio daquela área, e aqui fica só o ponteiro.
- Releia e ajuste este arquivo depois das primeiras semanas de uso — as seções que você mais usa vão ficar óbvias, e as que sobram podem ser cortadas.
