import json
import os
import pathlib
import platform
import resource
import signal
import gzip
import shutil
import subprocess

root=pathlib.Path(__file__).resolve().parents[1]
version=subprocess.check_output(['ocamlc','-version'],text=True).strip()
work=root/'.cache/bench'/version
work.mkdir(parents=True,exist_ok=True)
prefix=root/'.cache/traces'/version/'installed'
env=dict(os.environ,OCAMLPATH=str(prefix/'lib'))
results={}
for backend in ['native','jsoo','melange','typed-array']:
    if backend=='typed-array':
        args=['node','--max-old-space-size=256',str(root/'tools/direct_bench.cjs')]
        entry=root/'tools/direct_bench.cjs'
    else:
        path=work/backend
        path.mkdir(exist_ok=True)
        shutil.copyfile(root/'test/benchmark.ml',path/'benchmark.ml')
        (path/'backend.ml').write_text('module Bigarray = '+('Melange_bigarray' if backend=='melange' else 'Bigarray')+'\n')
        cpu_clock='function() { const t=process.cpuUsage(); return (t.user+t.system)/1e6; }'
        if backend=='melange':
            clock='let cpu_time : unit -> float = [%mel.raw {|'+cpu_clock+'|}]\n'
        elif backend=='jsoo':
            clock='external cpu_time : unit -> float = "benchmark_cpu_time"\n'
            (path/'cpu_time.js').write_text('//Provides: benchmark_cpu_time\n'+cpu_clock.replace('function()', 'function benchmark_cpu_time()')+'\n')
        else:
            clock='let cpu_time = Sys.time\n'
        with (path/'backend.ml').open('a') as output:
            output.write(clock)
        (path/'dune-project').write_text('(lang dune 3.21)\n(using melange 1.0)\n')
        dune='(melange.emit (target output) (modules benchmark backend) (libraries melange-bigarray) (preprocess (pps melange.ppx)))' if backend=='melange' else '(executable (name benchmark) (modules benchmark backend) (modes '+('exe' if backend=='native' else 'js')+')'+(' (js_of_ocaml (javascript_files cpu_time.js))' if backend=='jsoo' else '')+')'
        (path/'dune').write_text(dune+'\n')
        subprocess.run(['dune','build','--root',str(path),'@all'],env=env,check=True,timeout=600)
        entry=path/('_build/default/output/benchmark.js' if backend=='melange' else '_build/default/benchmark.'+('exe' if backend=='native' else 'bc.js'))
        args=[str(entry)] if backend=='native' else ['node','--max-old-space-size=256',str(entry)]
    output_file=work/(backend+'.tsv')
    with output_file.open('w') as stdout:
        proc=subprocess.Popen(args,stdout=stdout,start_new_session=True)
        def timeout(signum, frame):
            os.killpg(proc.pid,signal.SIGKILL)
            raise TimeoutError('benchmark exceeded 120 seconds')
        signal.signal(signal.SIGALRM,timeout)
        signal.alarm(120)
        _,status,usage=os.wait4(proc.pid,0)
        signal.alarm(0)
        proc.returncode=os.waitstatus_to_exitcode(status)
        if proc.returncode:
            raise subprocess.CalledProcessError(proc.returncode,args)
    output=output_file.read_text()
    bundle=work/(backend+'.bundle.js')
    if backend in ['melange','jsoo','typed-array']:
        subprocess.run(['node','-e',
          "require('esbuild').buildSync({entryPoints:[process.argv[1]],outfile:process.argv[2],bundle:true,minify:true,platform:'node'});",str(entry),str(bundle)],check=True,timeout=60)
    results[backend]={'measurements':{line.split('\t')[0]:{'median_cpu_seconds':float(line.split('\t')[1]),'bytes':int(line.split('\t')[2])} for line in output.splitlines()},
      'peak_rss_kib':usage.ru_maxrss,'entry_bytes':entry.stat().st_size,
      'clock':'Sys.time (CPU)' if backend=='native' else 'process.cpuUsage (CPU)'}
    if bundle.exists():
        results[backend].update({'standalone_minified_bundle_bytes':bundle.stat().st_size,
          'standalone_bundle_gzip_bytes':len(gzip.compress(bundle.read_bytes()))})
report={'ocaml':version,'node':subprocess.check_output(['node','--version'],text=True).strip(),
 'hardware':{'arch':platform.machine(),'cpu':next((line.split(':',1)[1].strip() for line in pathlib.Path('/proc/cpuinfo').read_text().splitlines() if line.startswith(('model name','Hardware','Processor'))),'unknown'),
 'cores':os.cpu_count(),'cpuinfo':pathlib.Path('/proc/cpuinfo').read_text().split('\n\n')[0]},'samples':7,'warmup':1,'results':results,
 'source':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
 'scope':'Installed Melange library; CPU time; typed-array Int64 control sums paired lanes without boxes. Entry size excludes imported modules; standalone minified Node bundles include all imports.'}
out=root/'.cache/reports'/version/'bench.json'
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
