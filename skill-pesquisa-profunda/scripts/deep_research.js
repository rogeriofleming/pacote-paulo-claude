export const meta = {
  name: 'pesquisa-profunda',
  description: 'Pesquisa profunda multi-fonte v2 — com CHECKPOINT EM DISCO (cada agente salva seu resultado na hora), teto duro de ~24 agentes e retomada. Substitui a deep-research oficial.',
  whenToUse: 'Pesquisa profunda, factual, multi-fonte. Invocar via SKILL pesquisa-profunda (ela define pasta de destino e retomada). args = {pergunta, pasta}.',
  phases: [
    { title: 'Scope', detail: 'Decompõe a pergunta em 4 ângulos de busca' },
    { title: 'Search', detail: '4 agentes WebSearch, um por ângulo (effort low)' },
    { title: 'Fetch', detail: 'Dedup de URL, fetch de até 10 fontes; cada agente SALVA a fonte em disco' },
    { title: 'Verify', detail: 'Até 8 claims centrais, 1 verificador cético cada (não 3 votos)' },
    { title: 'Synthesize', detail: 'Síntese com citações; o agente ESCREVE o RELATORIO.md antes de retornar' },
  ],
}

// ══ Por que este script substitui a deep-research oficial ══
// A oficial, num caso real, rodou 2x numa mesma pesquisa e:
//   run 1: 100 agentes, 1,5M tokens — os 75 verificadores (25 claims × 3 votos) morreram TODOS por limite de sessão.
//   run 2: 102 agentes, 3,5M tokens — timeout de 100s abandonou 18/25 vereditos VÁLIDOS; síntese falhou; nada em disco.
// Correções: teto ~24 agentes (4 ângulos + 10 fontes + 8 vereditos de 1 voto + scope + síntese);
// cada agente persiste o próprio resultado em disco NA HORA (sessão pode morrer que nada se perde);
// timeout largo (4-5 min) só como backstop — o limite real de trabalho está no PROMPT de cada agente;
// guarda de budget antes das fases caras.

// ── Escala (teto duro) ──
const N_ANGULOS = 4
const MAX_FETCH = 10
const MAX_VERIFY = 8
const FETCH_TIMEOUT_MS = 240_000   // backstop, não guilhotina: fetch legítimo leva 1-3 min
const VERIFY_TIMEOUT_MS = 300_000  // verificador legítimo (busca+análise) leva até ~5 min
const RESERVA_VERIFY = 40_000      // tokens mínimos no budget pra valer a pena verificar
const RESERVA_SINTESE = 15_000

// ── Entrada: args = {pergunta, pasta} (ou string = só a pergunta, ou JSON serializado de {pergunta,pasta}) ──
let ARGS = args
if (typeof ARGS === 'string') {
  try { const parsed = JSON.parse(ARGS); if (parsed && typeof parsed === 'object') ARGS = parsed } catch {}
}
const QUESTION = (typeof ARGS === 'string' ? ARGS : (ARGS && ARGS.pergunta) || '').trim()
if (!QUESTION) {
  return { error: 'Sem pergunta. Invocar com args: {pergunta: "...", pasta: "caminho/da/pesquisa"}.' }
}
const slugify = s => s.normalize('NFD').replace(new RegExp('[\u0300-\u036f]', 'g'), '').toLowerCase()
  .replace(/[^a-z0-9]+/g, ' ').trim().split(/\s+/).slice(0, 5).join('-')
const DIR = ((typeof ARGS === 'object' && ARGS && ARGS.pasta) || ('pesquisas/' + slugify(QUESTION))).replace(/[\\/]+$/, '')

// ── Timeout backstop. IMPORTANTE: Promise.race NÃO mata o agente (ele continua rodando e
// gastando em background) — só destrava o pipeline. Por isso o prompt de cada agente é quem
// limita o trabalho (máx 2 WebFetch, desistir de página lenta). Erros também caem no fallback. ──
const temTimer = typeof setTimeout === 'function'
function agenteSeguro(prompt, opts, fallback, ms) {
  const chamada = agent(prompt, opts).catch(e => {
    log('erro em ' + (opts.label || 'agente') + ': ' + (e && e.message || e))
    return fallback
  })
  if (!temTimer) return chamada
  let timer
  const timeout = new Promise(res => { timer = setTimeout(() => {
    log('TIMEOUT ' + (ms / 1000) + 's (backstop) — ' + (opts.label || 'agente'))
    res(fallback)
  }, ms) })
  return Promise.race([chamada, timeout]).finally(() => clearTimeout(timer))
}

const REGRAS = '\n\n## Regras duras\n' +
  '- NÃO crie subagentes nem workflows.\n' +
  '- No MÁXIMO 2 chamadas WebFetch no total. Página lenta, com erro ou paywall: desista DELA na hora e registre a falha — nunca insista na mesma URL.\n' +
  '- ANTES de retornar, salve seu resultado com a ferramenta Write no arquivo indicado (crie a pasta se preciso). Salve MESMO em caso de falha, registrando o que falhou.\n' +
  '- Sua resposta final é o dado estruturado pedido, não uma mensagem pra humano.'

// ── Schemas ──
const SCOPE_SCHEMA = { type: 'object', required: ['angles'], properties: {
  angles: { type: 'array', minItems: 3, maxItems: 4, items: { type: 'object', required: ['label', 'query'], properties: {
    label: { type: 'string' }, query: { type: 'string' }, rationale: { type: 'string' } } } } } }
const SEARCH_SCHEMA = { type: 'object', required: ['results'], properties: {
  results: { type: 'array', maxItems: 5, items: { type: 'object', required: ['url', 'title', 'relevance'], properties: {
    url: { type: 'string' }, title: { type: 'string' }, snippet: { type: 'string' }, relevance: { enum: ['high', 'medium', 'low'] } } } } } }
const EXTRACT_SCHEMA = { type: 'object', required: ['claims', 'sourceQuality'], properties: {
  sourceQuality: { enum: ['primary', 'secondary', 'blog', 'forum', 'unreliable'] },
  publishDate: { type: 'string' },
  claims: { type: 'array', maxItems: 5, items: { type: 'object', required: ['claim', 'quote', 'importance'], properties: {
    claim: { type: 'string' }, quote: { type: 'string' }, importance: { enum: ['central', 'supporting', 'tangential'] } } } } } }
const VERDICT_SCHEMA = { type: 'object', required: ['veredicto', 'evidencia'], properties: {
  veredicto: { enum: ['confirmado', 'refutado', 'incerto'] }, evidencia: { type: 'string' }, contraFonte: { type: 'string' } } }
const REPORT_SCHEMA = { type: 'object', required: ['summary', 'findings', 'caveats'], properties: {
  summary: { type: 'string' },
  findings: { type: 'array', items: { type: 'object', required: ['claim', 'confidence', 'sources'], properties: {
    claim: { type: 'string' }, confidence: { enum: ['high', 'medium', 'low'] },
    sources: { type: 'array', items: { type: 'string' } }, evidence: { type: 'string' } } } },
  caveats: { type: 'string' }, openQuestions: { type: 'array', items: { type: 'string' } } } }

// ── Fase 1: Scope ──
phase('Scope')
const scope = await agenteSeguro(
  'Decomponha esta pergunta de pesquisa em ' + N_ANGULOS + ' ângulos de busca web complementares e específicos (sem redundância).\n\n' +
  '## Pergunta\n' + QUESTION + '\n\n' +
  'Salve os ângulos escolhidos (com 1 linha de racional cada) em `' + DIR + '/01_escopo.md`.' + REGRAS,
  { label: 'scope', schema: SCOPE_SCHEMA }, null, VERIFY_TIMEOUT_MS)
if (!scope) return { error: 'Scope falhou — nada foi gasto além de 1 agente. Re-rodar.', dir: DIR }
log('Ângulos: ' + scope.angles.map(a => a.label).join(' · '))

// ── Dedup compartilhado entre buscadores ──
const normURL = u => { try { const p = new URL(u); return (p.hostname.replace(/^www\./, '') + p.pathname.replace(/\/$/, '')).toLowerCase() } catch { return u.toLowerCase() } }
const vistos = new Map()
const relRank = { high: 0, medium: 1, low: 2 }
let vagasFetch = MAX_FETCH
let nFonte = 0

// ── Fases 2+3: Search → dedup → Fetch (pipeline, sem barreira) ──
const resultadosBusca = await pipeline(
  scope.angles,

  (angle, _, i) => agenteSeguro(
    '## Buscador web: ' + angle.label + '\n\nPergunta de pesquisa: "' + QUESTION + '"\n' +
    'Seu ângulo: ' + angle.label + ' — ' + (angle.rationale || '') + '\nQuery sugerida: `' + angle.query + '`\n\n' +
    'Use WebSearch (pode refinar a query). Retorne os 4-5 resultados mais relevantes pra pergunta ORIGINAL, pulando SEO spam.\n' +
    'Salve a lista em `' + DIR + '/02_busca_' + (i + 1) + '.md`.' + REGRAS,
    { label: 'busca:' + angle.label, phase: 'Search', schema: SEARCH_SCHEMA, effort: 'low' }, null, FETCH_TIMEOUT_MS
  ).then(r => r && { angle: angle.label, results: r.results }),

  busca => {
    if (!busca) return []
    const ordenados = [...busca.results].sort((a, b) => relRank[a.relevance] - relRank[b.relevance])
    const novos = ordenados.filter(r => {
      const k = normURL(r.url)
      if (vistos.has(k) || vagasFetch <= 0) return false
      vistos.set(k, true); vagasFetch--
      return true
    })
    return parallel(novos.map(fonte => () => {
      let host = 'fonte'; try { host = new URL(fonte.url).hostname.replace(/^www\./, '') } catch {}
      nFonte++
      const arq = DIR + '/fontes/' + String(nFonte).padStart(2, '0') + '_' + host.replace(/[^a-z0-9.-]/gi, '') + '.md'
      return agenteSeguro(
        '## Extrator de fonte\n\nPergunta de pesquisa: "' + QUESTION + '"\n\n' +
        'Fonte: ' + fonte.url + ' (' + fonte.title + ', via ângulo ' + busca.angle + ')\n\n' +
        '1. WebFetch na URL (máx 2 tentativas NO TOTAL; falhou/paywall/lenta → registre a falha e encerre com claims: []).\n' +
        '2. Classifique a qualidade da fonte e anote a data de publicação se houver.\n' +
        '3. Extraia 2-5 claims FALSIFICÁVEIS relevantes à pergunta, cada um com citação literal da página e importância (central/supporting/tangential).\n' +
        '4. Salve TUDO (qualidade, data, claims com citações — ou o registro da falha) em `' + arq + '`.' + REGRAS,
        { label: 'fetch:' + host, phase: 'Fetch', schema: EXTRACT_SCHEMA, effort: 'low' },
        { claims: [], sourceQuality: 'unreliable', falhou: true }, FETCH_TIMEOUT_MS
      ).then(ext => ({ url: fonte.url, title: fonte.title, angle: busca.angle, arquivo: arq,
        sourceQuality: ext.sourceQuality, publishDate: ext.publishDate, falhou: !!ext.falhou,
        claims: (ext.claims || []).map(c => ({ ...c, sourceUrl: fonte.url, sourceQuality: ext.sourceQuality })) }))
    }))
  }
)

const fontes = resultadosBusca.flat().filter(Boolean)
const claims = fontes.flatMap(f => f.claims)
const impRank = { central: 0, supporting: 1, tangential: 2 }
const qualRank = { primary: 0, secondary: 1, blog: 2, forum: 3, unreliable: 4 }
const ranqueados = [...claims].sort((a, b) =>
  (impRank[a.importance] - impRank[b.importance]) || (qualRank[a.sourceQuality] - qualRank[b.sourceQuality]))
const aVerificar = ranqueados.slice(0, MAX_VERIFY)
const naoVerificados = ranqueados.slice(MAX_VERIFY)
log(fontes.length + ' fontes (' + fontes.filter(f => f.falhou).length + ' falhas) → ' + claims.length + ' claims → verificando top ' + aVerificar.length)

// ── Fase 4: Verify — 1 cético por claim (não 3 votos), com guarda de budget ──
phase('Verify')
let vereditos = []
const pularVerify = budget.total && budget.remaining() < RESERVA_VERIFY
if (pularVerify) log('BUDGET BAIXO (' + Math.round(budget.remaining() / 1000) + 'k) — pulando verificação; claims seguem como não-verificados')
if (!pularVerify && aVerificar.length > 0) {
  vereditos = (await parallel(aVerificar.map((c, i) => () =>
    agenteSeguro(
      '## Verificador cético\n\nSeja CÉTICO: tente REFUTAR este claim antes de aceitá-lo.\n\n' +
      'Pergunta de pesquisa: "' + QUESTION + '"\n' +
      'Claim: "' + c.claim + '"\nFonte: ' + c.sourceUrl + ' (' + c.sourceQuality + ')\nCitação de apoio: "' + c.quote + '"\n\n' +
      'Cheque: (1) a citação sustenta mesmo o claim? (2) UMA busca WebSearch por evidência contrária; (3) qualidade da fonte compatível com a força do claim? (4) está desatualizado? (5) é marketing/especulação?\n' +
      'veredicto: "confirmado" (sustentado e sem contradição), "refutado" (contradito ou não sustentado — evidência ESPECÍFICA obrigatória) ou "incerto".\n' +
      'Salve o veredito + evidência em `' + DIR + '/vereditos/' + String(i + 1).padStart(2, '0') + '.md`.' + REGRAS,
      { label: 'verifica:' + c.claim.slice(0, 35), phase: 'Verify', schema: VERDICT_SCHEMA, effort: 'medium' },
      null, VERIFY_TIMEOUT_MS
    ).then(v => ({ ...c, veredicto: v ? v.veredicto : 'incerto', evidencia: v ? v.evidencia : 'verificador falhou/timeout' }))
  ))).filter(Boolean)
} else {
  vereditos = aVerificar.map(c => ({ ...c, veredicto: 'incerto', evidencia: pularVerify ? 'verificação pulada (budget)' : '' }))
}
const confirmados = vereditos.filter(v => v.veredicto === 'confirmado')
const refutados = vereditos.filter(v => v.veredicto === 'refutado')
const incertos = vereditos.filter(v => v.veredicto === 'incerto')
log('Vereditos: ' + confirmados.length + ' confirmados · ' + refutados.length + ' refutados · ' + incertos.length + ' incertos')

// ── Fase 5: Synthesize — o agente ESCREVE o relatório em disco antes de retornar ──
phase('Synthesize')
const linha = c => '- "' + c.claim + '" (fonte: ' + c.sourceUrl + ', ' + c.sourceQuality + ')' + (c.evidencia ? ' — ' + c.evidencia : '')
const corpo =
  '## Confirmados (' + confirmados.length + ')\n' + confirmados.map(linha).join('\n') +
  '\n\n## Incertos (' + incertos.length + ')\n' + incertos.map(linha).join('\n') +
  '\n\n## Não verificados (' + naoVerificados.length + ')\n' + naoVerificados.map(linha).join('\n') +
  '\n\n## Refutados (' + refutados.length + ')\n' + refutados.map(linha).join('\n')
const report = await agenteSeguro(
  '## Síntese de pesquisa\n\nPergunta: "' + QUESTION + '"\n\n' + corpo + '\n\n' +
  '1. Funda claims duplicados/semelhantes (somando fontes), agrupe em achados que respondem a pergunta.\n' +
  '2. Confiança por achado: high (confirmado + múltiplas fontes) · medium (confirmado single-source ou incerto corroborado) · low (só não-verificados).\n' +
  '3. Sumário executivo de 3-5 frases; ressalvas (o que é fraco/velho); 2-4 perguntas abertas.\n' +
  '4. ESCREVA o relatório completo e legível em `' + DIR + '/RELATORIO.md` (título, data da pesquisa se conhecida, achados com fontes linkadas, ressalvas) — este arquivo é o produto principal.' + REGRAS,
  { label: 'sintese', schema: REPORT_SCHEMA }, null, VERIFY_TIMEOUT_MS)

const stats = { angulos: scope.angles.length, fontes: fontes.length, fontesFalha: fontes.filter(f => f.falhou).length,
  claims: claims.length, verificados: vereditos.length, confirmados: confirmados.length,
  refutados: refutados.length, incertos: incertos.length, naoVerificados: naoVerificados.length,
  agentes: 1 + scope.angles.length + fontes.length + (pularVerify ? 0 : aVerificar.length) + 1 }

if (!report) {
  return { question: QUESTION, dir: DIR,
    summary: 'Síntese falhou — mas TODO o material está salvo em ' + DIR + ' (fontes/, vereditos/). Sintetizar manualmente a partir dos arquivos; NÃO re-rodar a pesquisa.',
    confirmados: confirmados.map(linha), incertos: incertos.map(linha), naoVerificados: naoVerificados.map(linha), refutados: refutados.map(linha), stats }
}
return { question: QUESTION, dir: DIR, relatorio: DIR + '/RELATORIO.md', ...report, refutados: refutados.map(linha), stats }
