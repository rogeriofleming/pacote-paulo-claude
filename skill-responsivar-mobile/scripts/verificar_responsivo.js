#!/usr/bin/env node
/*
 * verificar_responsivo.js — mede overflow horizontal de uma página num browser REAL.
 *
 * Por página × largura, mede e reporta:
 *   - overflow horizontal: scrollWidth vs innerWidth (screenshot ENGANA; a medida é o critério)
 *     + lista os elementos culpados quando estoura a tela
 *   - erros de JavaScript (pageerror)
 * Sai com exit 0 só se TUDO passou (0 overflow, 0 erro JS) — dá pra usar em pipeline/loop.
 *
 * Uso:
 *   node verificar_responsivo.js <alvo> [alvo2 ...] [--larguras 320,360,375,414,430] [--espera 900]
 *   alvo = caminho de um arquivo .html  OU  URL (http://localhost:PORTA / https://...)
 *
 * Larguras padrão = 320,360,375,414,430 (o parque de celulares: 5" / 5.5" / 6"+).
 *
 * Dependência (instalar uma vez — ver COMO_USAR.md):
 *   npm i -D playwright && npx playwright install chromium
 * O script também funciona com o Chrome/Edge do sistema se você só tiver playwright-core.
 */
const fs = require('fs');
const path = require('path');

// --- resolver o motor do browser: playwright (baixa o próprio chromium) OU playwright-core.
// Devolve o objeto `chromium` do Playwright + o Chrome/Edge do sistema (se achado),
// pra usar como fallback caso o chromium baixado não exista.
function acharBrowser() {
  let chromium = null;
  try { ({ chromium } = require('playwright')); } catch (_) {}
  if (!chromium) { try { ({ chromium } = require('playwright-core')); } catch (_) {} }
  if (!chromium) {
    console.error('ERRO: nem "playwright" nem "playwright-core" encontrados.');
    console.error('Instale com:  npm i -D playwright && npx playwright install chromium');
    process.exit(2);
  }
  const cands = [
    // Windows
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
    // macOS
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    // Linux
    '/usr/bin/google-chrome',
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
    '/usr/bin/microsoft-edge',
  ];
  const exeSistema = cands.find((c) => fs.existsSync(c)) || null;
  return { chromium, exeSistema };
}

// Sobe o browser: 1º tenta o chromium que o Playwright baixou; se não existir,
// cai pro Chrome/Edge do sistema. Só falha se nenhum dos dois estiver disponível.
async function abrirBrowser({ chromium, exeSistema }) {
  try {
    return await chromium.launch({ headless: true });
  } catch (e1) {
    if (exeSistema) {
      try { return await chromium.launch({ headless: true, executablePath: exeSistema }); } catch (_) {}
    }
    console.error('ERRO: não consegui abrir o Chromium.');
    console.error('Rode:  npx playwright install chromium   (ou instale o Google Chrome)');
    console.error('Detalhe: ' + String(e1).split('\n')[0]);
    process.exit(2);
  }
}

// --- args
const args = process.argv.slice(2);
const alvos = [];
let larguras = [320, 360, 375, 414, 430]; // parque de celulares (5" / 5.5" / 6"+)
let espera = 900; // ms — deixa animações de entrada terminarem antes de medir
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--larguras') larguras = args[++i].split(',').map(Number);
  else if (args[i] === '--espera') espera = Number(args[++i]);
  else alvos.push(args[i]);
}
if (!alvos.length) {
  console.error('Uso: node verificar_responsivo.js <arquivo.html|url> [...] [--larguras 320,360,375,414,430] [--espera 900]');
  process.exit(2);
}

const motor = acharBrowser();

function urlDoAlvo(a) {
  if (/^https?:\/\//i.test(a)) return a;
  const abs = path.resolve(a).replace(/\\/g, '/');
  if (!fs.existsSync(abs)) { console.error(`ERRO: arquivo não existe: ${abs}`); process.exit(2); }
  return 'file:///' + abs;
}

(async () => {
  const browser = await abrirBrowser(motor);
  let falhas = 0;
  for (const alvo of alvos) {
    const url = urlDoAlvo(alvo);
    for (const w of larguras) {
      const ctx = await browser.newContext({ viewport: { width: w, height: 900 } });
      const page = await ctx.newPage();
      const errosJS = [];
      page.on('pageerror', (e) => errosJS.push(String(e).split('\n')[0]));
      try {
        await page.goto(url, { waitUntil: 'load', timeout: 45000 });
      } catch (e) {
        console.log(`${alvo} @${w}px  ❌ NÃO CARREGOU: ${String(e).split('\n')[0]}`);
        falhas++; await ctx.close(); continue;
      }
      await page.waitForTimeout(espera);
      const m = await page.evaluate(() => ({
        scroll: document.documentElement.scrollWidth,
        body: document.body ? document.body.scrollWidth : 0,
        inner: window.innerWidth,
      }));
      const overflow = m.scroll > m.inner || m.body > m.inner;
      const ok = !overflow && errosJS.length === 0;
      if (!ok) falhas++;
      console.log(
        `${alvo} @${w}px  scroll=${m.scroll} body=${m.body} inner=${m.inner}  ` +
        `${overflow ? '❌ OVERFLOW' : 'ok'} · errosJS=${errosJS.length}  ${ok ? '✅' : '❌'}`
      );
      if (overflow) {
        const culpados = await page.evaluate(() => {
          const iw = window.innerWidth, out = [];
          document.querySelectorAll('*').forEach((el) => {
            const r = el.getBoundingClientRect();
            if (r.right > iw + 1 || r.left < -1)
              out.push(`<${el.tagName.toLowerCase()}${el.className ? ' .' + String(el.className).split(' ')[0] : ''}> right=${Math.round(r.right)} left=${Math.round(r.left)}`);
          });
          return out.slice(0, 10);
        });
        culpados.forEach((c) => console.log(`     culpado: ${c}`));
      }
      errosJS.forEach((e) => console.log(`     erroJS: ${e}`));
      await ctx.close();
    }
  }
  await browser.close();
  console.log(falhas === 0
    ? `\n✅ TUDO PASSOU (${alvos.length} alvo(s) × ${larguras.join('/')}px: 0 overflow, 0 erro JS)`
    : `\n❌ ${falhas} medida(s) REPROVADA(s) — consertar e rodar de novo`);
  process.exit(falhas === 0 ? 0 : 1);
})();
