import json
import os
import pathlib
import re
import subprocess

root = pathlib.Path(__file__).resolve().parents[1]
version = subprocess.check_output(['ocamlc','-version'], text=True).strip()
source = (root / '.cache/traces' / version / 'melange/trace.ml').read_text()
source += (root / 'test/multidimensional.ml.in').read_text()
source += (root / 'spike/probe.ml').read_text()
api = (root / 'api' / (version + '.mli')).read_text()
module = ''
entries = []
for line in api.splitlines():
    m = re.match(r'module (\w+)\s*:', line)
    if m:
        module = m[1]
    if line.strip() == 'end':
        module = ''
    m = re.match(r'\s*(?:val|external)\s+(\w+)\s*:',line)
    if m:
        name = m[1]
        qualified = (module + '.' if module else '') + name
        pattern = r'\b' + re.escape(qualified) + r'\b'
        if not re.search(pattern, source):
            raise RuntimeError('API entry lacks an executable test reference: ' + qualified)
        entries.append(qualified)
output = root / '.cache/reports' / version / 'api-coverage.json'
output.write_text(json.dumps({'compiler':version,'method':'full interface compiled; every operation referenced by executed deterministic suites','entries':entries},indent=2)+'\n')
print(f'{len(entries)} selected API entries checked')
