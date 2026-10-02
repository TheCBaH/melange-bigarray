"""Rebuild a real dependency and clients against installed artifacts."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess

root = pathlib.Path(__file__).resolve().parents[1]
version = subprocess.check_output(['ocamlc', '-version'], text=True).strip()
work = root / '.cache/clients' / version
if work.exists():
    shutil.rmtree(work)
work.mkdir(parents=True)
reports = root / '.cache/reports' / version
reports.mkdir(parents=True, exist_ok=True)
prefix = pathlib.Path(os.environ.get('CLIENT_PREFIX', str(root / '.cache/traces' / version / 'installed')))
env = dict(os.environ, OCAMLPATH=str(prefix / 'lib'))
(work / 'dune-project').write_text('(lang dune 3.21)\n(using melange 1.0)\n')
for name in ['client', 'generic']:
    shutil.copyfile(root / 'test' / (name + '.ml'), work / (name + '.ml'))
source = root / '.cache/oracles/dbuenzli-bytesrw/0.3.0/src'
for name in ['bytesrw','bytesrw_fmt']:
    for suffix in ['ml','mli']:
        shutil.copyfile(source / (name+'.'+suffix),work / (name+'.'+suffix))
(work / 'dune').write_text('''(library (name dependency) (wrapped false)
 (modules bytesrw bytesrw_fmt) (flags :standard -warn-error -a) (modes melange) (libraries melange-bigarray.compat))
(melange.emit (target output) (modules client generic)
 (libraries dependency melange-bigarray) (preprocess (pps melange.ppx)))
''')
patches = []
# Keep this patch explicit: Melange has no Printexc.register_printer.
original = (work / 'bytesrw.ml').read_text()
needle = 'Printexc.register_printer printer'
assert original.count(needle) == 1
(work / 'bytesrw.ml').write_text(original.replace(needle, 'ignore printer'))
patches.append({'path': 'src/bytesrw.ml', 'before': needle, 'after': 'ignore printer'})
subprocess.run(['dune', 'build', '--root', str(work), '@all'], env=env, check=True, timeout=600)
outputs = {}
for name in ['client','generic']:
    result = subprocess.run(['node', '--max-old-space-size=256', str(work / '_build' / 'default/output' / (name+'.js'))], capture_output=True, text=True, check=True, timeout=60)
    outputs[name] = result.stdout
    (reports / (name+'-node.txt')).write_text(result.stdout)
# Marshal serialization uses an unsupported Melange primitive.
(work / 'marshal.ml').write_text('let encode a = Marshal.to_string a []\n')
(work / 'dune').write_text((work / 'dune').read_text()+'(melange.emit (target marshal) (modules marshal) (libraries melange-bigarray))\n')
result = subprocess.run(['dune','build','--root',str(work),'marshal/marshal.js'],env=env,capture_output=True,text=True,timeout=60)
assert result.returncode != 0 and 'caml_output_value_to_string' in result.stderr, result.stderr
(reports / 'marshal-negative.txt').write_text(result.stderr)
(reports / 'clients.json').write_text(json.dumps({'ocaml':version, 'dependency':'bytesrw 0.3.0',
 'revision':'347a5e9eaffb2f9b7015ea4aa13b98f959320b4a', 'patches':patches,
 'patched_source_sha256':hashlib.sha256((work/'bytesrw.ml').read_bytes()).hexdigest(),
 'installed_prefix':str(prefix),'outputs':outputs,'marshal':'expected compiler rejection'},indent=2)+'\n')
print(outputs['client'],end='')
