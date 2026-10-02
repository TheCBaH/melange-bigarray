"""Build the committed source archive in a fresh opam root, then offline clients."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tarfile
import urllib.request
import re
import platform

root=pathlib.Path(__file__).resolve().parents[1]
version=subprocess.check_output(['opam','exec','--','ocamlc','-version'],text=True).strip()
matrix=json.loads((root/'tools/matrix.json').read_text())['include']
melange=next(row['melange'] for row in matrix if row['ocaml']==version)
locks=json.loads((root/'tools/toolchain.lock.json').read_text())
sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
reports=root/'.cache/reports'/version
reports.mkdir(parents=True,exist_ok=True)
work=root/'.cache/distribution'/version
if work.exists():
    shutil.rmtree(work)
work.mkdir(parents=True)
archive=reports/'source.tar'
with archive.open('wb') as output:
    subprocess.run(['git','archive','--format=tar',sha],stdout=output,check=True)
source=work/'source'
source.mkdir()
with tarfile.open(archive) as tar:
    members=tar.getnames()
    assert all(not name.startswith(('.cache/','_build','node_modules/')) for name in members)
    tar.extractall(source,filter='data')
for name in ['LICENSE','licenses/OCaml-LICENSE','licenses/OCaml-notice.txt','melange-bigarray.opam']:
    assert name in members
env=dict(os.environ,OPAMROOT=str(work/'opam'),OPAMSWITCH='v1',OPAMYES='1',OPAMJOBS=str(min(4,os.cpu_count() or 1)))
env.pop('OCAMLPATH',None)
def run(args,**kw):
    subprocess.run(args,env=env,check=True,timeout=1800,**kw)
try:
    metadata=work/'metadata.tar.gz'
    urllib.request.urlretrieve('https://github.com/ocaml/opam-repository/archive/'+locks['opam_repository']+'.tar.gz',metadata)
    with tarfile.open(metadata) as tar:
        tar.extractall(work,filter='data')
    repository=work/('opam-repository-'+locks['opam_repository'])
    run(['opam','init','--bare','--no-setup','--disable-sandboxing','pinned',str(repository)])
    run(['opam','switch','create','v1','ocaml-base-compiler.'+version])
    run(['opam','install','dune.'+locks['dune'],'melange.'+melange,'conf-python-3.'+locks['conf-python-3']])
    run(['opam','clean','-a','-c','-s','--logs'])
    packages=subprocess.check_output(['opam','list','--installed','--columns=name,version','--short'],env=env,text=True)
    assert ('melange '+melange) in packages or any(line.split()==['melange',melange] for line in packages.splitlines())
    run(['opam','pin','add','--no-action','melange-bigarray',str(source)])
    # No network for package build/install or any client execution.
    run(['bash',str(root/'tools/offline.sh'),'opam','install','melange-bigarray'])
    installed=work/'opam/v1'
    client_env=dict(env,CLIENT_PREFIX=str(installed),CLIENT_WORK=str(work/'clients'))
    subprocess.run(['bash',str(root/'tools/offline.sh'),'opam','exec','--','python3',str(root/'tools/clients.py')],env=client_env,check=True,timeout=600)
    subprocess.run(['bash',str(root/'tools/offline.sh'),'node',str(root/'tools/client_browser.cjs')],env=dict(client_env,OCAML_VERSION=version),check=True,timeout=180)
    assert json.loads((reports/'clients.json').read_text())['installed_prefix'] == str(installed)
    lib=installed/'lib/melange-bigarray'
    files=sorted(str(p.relative_to(installed)) for base in [installed/'lib/melange-bigarray',installed/'doc/melange-bigarray'] for p in base.rglob('*') if p.is_file())
    assert (lib/'META').exists() and any(name.endswith('.cmj') for name in files)
    meta=(lib/'META').read_text()
    assert not any(name in meta for name in ['safetensors','mltorch','bytesrw'])
    assert (installed/'doc/melange-bigarray/LICENSE').exists()
    runtime=work/'clients/_build/default/output'
    closure={}
    for js in runtime.rglob('*.js'):
        if not js.is_file():
            continue
        imports=re.findall(r'require\([\'"]([^\'"]+)[\'"]\)',js.read_text())
        for target in imports:
            if target.startswith('.'):
                assert (js.parent/target).exists(), 'missing runtime import: '+target
            else:
                if target.split('/')[0] in ['melange','melange.js','melange-bigarray','melange-bigarray.compat']:
                    assert (runtime/'node_modules'/target).exists(), 'missing installed runtime module: '+target
                else:
                    assert target.startswith('node:') or target in ['fs','path','util'], 'unexpected external runtime dependency: '+target
        closure[str(js.relative_to(runtime))]={'sha256':hashlib.sha256(js.read_bytes()).hexdigest(),'imports':imports}
    assert 'node_modules/melange-bigarray/melange_bigarray.js' in closure
    report={'source':sha,'dirty':bool(subprocess.check_output(['git','status','--porcelain'],text=True)),
      'ocaml':version,'melange':melange,'python':platform.python_version(),'opam_repository':locks['opam_repository'],
      'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
      'metadata_archive_sha256':hashlib.sha256(metadata.read_bytes()).hexdigest(),
      'fresh_compiler':True,'network_disabled_install_and_clients':True,'packages':packages,
      'source_members':members,'installed_files':files,'META':meta,'runtime_closure':closure,'private_root_deleted_after_run':True}
    (reports/'install.json').write_text(json.dumps(report,indent=2)+'\n')
finally:
    shutil.rmtree(work)
