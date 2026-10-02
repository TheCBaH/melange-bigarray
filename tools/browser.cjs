const fs = require('node:fs');
const path = require('node:path');
const esbuild = require('esbuild');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const work = path.join(root, '.cache/traces', process.env.OCAML_VERSION);
const reports = path.join(root, '.cache/reports', process.env.OCAML_VERSION);
(async () => {
  await esbuild.build({entryPoints: [path.join(work, 'melange/_build/default/output/trace.js')],
    bundle: true, platform: 'browser', outfile: path.join(work, 'melange.bundle.js')});
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox', '--js-flags=--max-old-space-size=256']});
  try {
    for (const backend of ['jsoo','melange']) {
      const page = await browser.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(String(e)));
      await page.evaluate(() => {
        window.stdout = []; window.stderr = [];
        console.log = (...args) => window.stdout.push(args.join(' '));
        console.error = (...args) => window.stderr.push(args.join(' '));
      });
      const file = backend === 'jsoo' ? 'jsoo/_build/default/trace.bc.js' : 'melange.bundle.js';
      await page.addScriptTag({path: path.join(work, file)});
      if (errors.length) throw Error(errors.join('\n'));
      const result = await page.evaluate(() => ({stdout: window.stdout.join('\n')+'\n', stderr: window.stderr.join('\n')+'\n'}));
      if (Buffer.byteLength(result.stdout) > 16*1024*1024) throw Error('browser payload exceeds 16 MiB');
      fs.writeFileSync(path.join(reports, backend+'-chromium.tsv'), result.stdout);
      fs.writeFileSync(path.join(reports, backend+'-chromium.stderr'), result.stderr);
      fs.writeFileSync(path.join(reports, 'chromium-version.txt'), browser.version()+'\n');
      await page.close();
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
