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
  const interopEntry=path.join(work,'interop-entry.cjs');
  fs.writeFileSync(interopEntry, `globalThis.InteropTest={B:require(${JSON.stringify(path.join(work,'melange/_build/default/output/node_modules/melange-bigarray/melange_bigarray.js'))}),run:require(${JSON.stringify(path.join(root,'tools/interop_cases.cjs'))})};`);
  await esbuild.build({entryPoints:[interopEntry],bundle:true,platform:'browser',outfile:path.join(work,'interop.bundle.js')});
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox', '--js-flags=--max-old-space-size=256', '--enable-features=SharedArrayBuffer']});
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
    const page=await browser.newPage();
    await page.addScriptTag({path:path.join(work,'interop.bundle.js')});
    const interop=await page.evaluate(() => {
      const frame=document.createElement('iframe'); document.body.append(frame);
      return InteropTest.run(InteropTest.B,code=>frame.contentWindow.eval(code));
    });
    interop.chromium=browser.version();
    fs.writeFileSync(path.join(reports,'interop-chromium.json'),JSON.stringify(interop,null,2)+'\n');
    await page.close();
    for (const name of ['client','generic']) {
      const input=path.join(root,'.cache/clients',process.env.OCAML_VERSION,'_build/default/output',name+'.js');
      const output=path.join(work,name+'.bundle.js');
      await esbuild.build({entryPoints:[input],bundle:true,platform:'browser',outfile:output});
      const client=await browser.newPage();
      const errors=[];
      client.on('pageerror',e=>errors.push(String(e)));
      await client.evaluate(()=>{window.stdout=[];console.log=(...args)=>window.stdout.push(args.join(' '));});
      await client.addScriptTag({path:output});
      if(errors.length) throw Error(errors.join('\n'));
      const result=await client.evaluate(()=>window.stdout.join('\n')+'\n');
      if(result!==fs.readFileSync(path.join(reports,name+'-node.txt'),'utf8')) throw Error(name+' browser mismatch');
      fs.writeFileSync(path.join(reports,name+'-chromium.txt'),result);
      await client.close();
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
