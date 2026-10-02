"""Reproduce a differential failure, delete operations and reduce dimensions."""
import json
import os
import pathlib
import subprocess
import sys

failure_path = pathlib.Path(sys.argv[1]).resolve()
failure = json.loads(failure_path.read_text())
root = pathlib.Path(__file__).resolve().parents[1]
report_dir = failure_path.parent / 'replay'
report_dir.mkdir(exist_ok=True)
candidate = report_dir / 'candidate.json'
original = {'id':failure['id'],'skip':{'vector':[],'matrix':[]},'shape':{}}
attempts = 0

def fails(config):
    global attempts
    attempts += 1
    candidate.write_text(json.dumps(config,indent=2)+'\n')
    (report_dir/'failure.json').unlink(missing_ok=True)
    env = dict(os.environ, TRACE_REPLAY=str(candidate), REPORT_DIR=str(report_dir))
    with (report_dir/'execution.log').open('w') as output:
        result = subprocess.run(['make','test.differential'],cwd=root,env=env,
                                stdout=output,stderr=subprocess.STDOUT,timeout=120)
    if result.returncode == 0:
        return False
    mismatch=report_dir/'failure.json'
    if not mismatch.exists():
        raise RuntimeError('replay failed to execute; see '+str(report_dir/'execution.log'))
    result_failure=json.loads(mismatch.read_text())
    return result_failure.get('id') == failure['id'] and result_failure['backend'] == failure['backend']

if not fails(original):
    raise RuntimeError('original failure did not reproduce')
best = original
# Bisect rejected deletions; accepted chunks need no individual retries.
def delete(domain, chunk):
    global best
    if attempts >= 48:
        return
    next_config=json.loads(json.dumps(best))
    next_config['skip'][domain]=sorted(set(best['skip'][domain]+chunk))
    if next_config == best:
        return
    if fails(next_config):
        best=next_config
    elif len(chunk)>1:
        middle=len(chunk)//2
        delete(domain,chunk[:middle])
        delete(domain,chunk[middle:])

for domain in ['vector','matrix']:
    delete(domain,list(range(1,25)))
for domain, shapes in [('vector',[[1],[2]]),('matrix',[[0,0],[1,1],[1,2],[2,1]])]:
    for shape in shapes:
        next_config=json.loads(json.dumps(best))
        next_config['shape'][domain]=shape
        if fails(next_config):
            best=next_config
            break
final = failure_path.parent/'minimized.json'
assert fails(best), 'minimized failure no longer reproduces'
final.write_text(json.dumps(best,indent=2)+'\n')
(failure_path.parent/'shrink.json').write_text(json.dumps({'attempts':attempts,'original':original,
 'minimized':best,'failure':failure,'replay':'make test.offline TRACE_REPLAY='+str(final)},indent=2)+'\n')
print('Retained minimized replay:',final)
