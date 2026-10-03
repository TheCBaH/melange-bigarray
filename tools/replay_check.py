import json
import os
import pathlib
import subprocess

root=pathlib.Path(__file__).resolve().parents[1]
version=subprocess.check_output(['ocamlc','-version'],text=True).strip()
reports=root/'.cache/reports'/version/'replay-check'
reports.mkdir(parents=True,exist_ok=True)
config=reports/'input.json'
config.write_text(json.dumps({'id':0,'shape':{'vector':[2],'matrix':[1,1]},
 'skip':{'vector':[1,3],'matrix':[2,4]}},indent=2)+'\n')
env=dict(os.environ,TRACE_REPLAY=str(config),REPORT_DIR=str(reports))
subprocess.run(['make','test.differential'],cwd=root,env=env,check=True,timeout=180)
# A deliberate lost write verifies detection, operation deletion and shape shrinking.
if version=='5.5.1':
    fault=reports/'fault'
    fault.mkdir(exist_ok=True)
    config.write_text(json.dumps({'id':0})+'\n')
    env.update(REPORT_DIR=str(fault),TRACE_TEST_FAULT='drop-vector-17')
    (fault/'failure.json').unlink(missing_ok=True)
    result=subprocess.run(['make','test.differential'],cwd=root,env=env,timeout=180)
    assert result.returncode and (fault/'failure.json').exists()
    subprocess.run(['python3',str(root/'tools/shrink.py'),str(fault/'failure.json')],cwd=root,env=env,check=True,timeout=600)
    minimized=json.loads((fault/'minimized.json').read_text())
    assert 17 not in minimized['skip']['vector']
    assert len(minimized['skip']['vector'])==23
    assert len(minimized['skip']['matrix'])==24
    assert minimized['shape'], 'shape reduction was not exercised'
    (reports/'selftest.json').write_text(json.dumps({'intentional_fault':'Melange test backend drops vector operation 17',
      'detected':True,'minimized':minimized,'real_library_failure':False},indent=2)+'\n')
