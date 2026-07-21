# Harness multiagente — modo pesado do Fable Mode

> Quando usar: tarefa grande/crítica (auditoria ampla, revisão extensa, pesquisa profunda, migração) E a sessão tem a tool `Agent` (ou `Task`) disponível. Custo alto em tokens — usar quando a exaustividade importa mais que o custo.
>
> **O princípio que transfere tudo:** *quem verifica não pode ser quem fez.* O autor de um rascunho carrega o viés do rascunho; um subagente cético, que recebe só a afirmação e a instrução de derrubá-la, enxerga o que o autor não enxerga. Todos os padrões abaixo são variações disso.

## Padrão 1 — Verificação adversarial (o mais usado)

Para cada achado/afirmação importante do trabalho principal:

1. Spawnar 3 subagentes independentes, cada um com o prompt: *"Tente REFUTAR esta afirmação: [afirmação + contexto mínimo]. Procure a evidência que a derruba. Na dúvida, considere refutada. Responda: refutada sim/não + evidência."*
2. **Não passar o raciocínio do autor** — só a afirmação. Passar o raciocínio contamina o verificador com o mesmo viés.
3. ≥2 de 3 refutam → o achado morre (ou volta pra investigação). Sobreviveu → está confirmado de verdade.

Variante mais barata: 1 verificador só, mas com lente explícita ("verifique se REPRODUZ", "verifique a SEGURANÇA", "verifique o CÁLCULO").

## Padrão 2 — Lentes diversas (em vez de redundância)

Quando um achado pode falhar de MAIS de um jeito, 3 verificadores idênticos desperdiçam — dar a cada um uma **lente distinta**: correção, segurança, performance, "isso reproduz?". Diversidade pega modos de falha que redundância não pega.

## Padrão 3 — Painel de juízes (decisões de design/estratégia)

1. Gerar N abordagens independentes por subagentes com ângulos diferentes (ex.: "priorize simplicidade", "priorize risco mínimo", "priorize o usuário final") — cada um SEM ver os outros.
2. Juízes paralelos pontuam com critérios explícitos.
3. Sintetizar a partir do vencedor, enxertando as melhores ideias dos perdedores.

Vence o "uma tentativa iterada" sempre que o espaço de solução é largo.

## Padrão 4 — Loop-até-secar (descoberta de tamanho desconhecido)

Bugs, inconsistências, casos de borda — não se sabe quantos existem. Contador fixo ("ache 10") erra a cauda:

1. Rodada de buscadores paralelos, cada um por um ângulo diferente (por arquivo, por conteúdo, por entidade, por período).
2. Dedupe contra TUDO que já foi visto (inclusive achados rejeitados — senão eles voltam toda rodada e o loop nunca converge).
3. K rodadas consecutivas sem achado novo (K=2) → secou, parar.

## Padrão 5 — Crítico de completude (fecho de qualquer harness)

Um subagente final com a pergunta: *"O que está FALTANDO neste trabalho — ângulo não varrido, afirmação não verificada, fonte não lida?"* O que ele achar vira a próxima rodada. É o guard-rail contra "cobri tudo" que não cobriu.

## Regras de montagem

- Subagente recebe **contexto mínimo e instrução de retorno estruturado** ("responda JSON: {refutada, evidencia}") — não a conversa inteira.
- Buscadores/verificadores independentes → spawnar **em paralelo na mesma rodada**.
- Se o harness limitou cobertura (top-N, amostragem) → **declarar o que ficou de fora** na entrega. Truncamento silencioso vira "cobri tudo" falso.
- Sem tool de subagente na sessão → degradar com dignidade: fazer o ataque adversarial da Fase 4 inline, com releitura dirigida e recomputação — nunca fingir que o harness rodou.
