import json
import pathlib

rows=json.loads((pathlib.Path(__file__).parent/'matrix.json').read_text())['include']
print(json.dumps({'include':[dict(row,runner=runner,engine=engine)
 for row in [rows[0],rows[-1]]
 for runner in ['ubuntu-latest','ubuntu-24.04-arm']
 for engine in ['chromium','firefox','webkit']]}))
