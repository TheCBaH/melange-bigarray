const fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright'),esbuild=require('esbuild');
const root=path.resolve(__dirname,'..'),version=process.env.OCAML_VERSION;
const reports=process.env.REPORT_DIR||path.join(root,'.cache/reports',version);
(async()=>{
  const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  try {
    for(const name of ['client','generic']) {
      const dir=process.env.CLIENT_WORK||path.join(root,'.cache/clients',version);
      const output=path.join(dir,name+'.bundle.js');
      await esbuild.build({entryPoints:[path.join(dir,'_build/default/output',name+'.js')],bundle:true,platform:'browser',outfile:output});
      const page=await browser.newPage(),errors=[];
      page.on('pageerror',e=>errors.push(String(e)));
      await page.evaluate(()=>{window.stdout=[];console.log=(...args)=>window.stdout.push(args.join(' '));});
      await page.addScriptTag({path:output});
      if(errors.length) throw Error(errors.join('\n'));
      const result=await page.evaluate(()=>window.stdout.join('\n')+'\n');
      if(result!==fs.readFileSync(path.join(reports,name+'-node.txt'),'utf8')) throw Error(name+' Chromium mismatch');
      fs.writeFileSync(path.join(reports,name+'-chromium.txt'),result);
      await page.close();
    }
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
