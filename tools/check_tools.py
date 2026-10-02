import json
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parents[1]
version = subprocess.check_output(["ocamlc", "-version"], text=True).strip()
expected = dict(line.split() for line in (root / "tools" / ("opam-" + version + ".lock")).read_text().splitlines())
actual = dict(line.split() for line in subprocess.check_output(["opam", "list", "--installed", "--columns=name,version", "--short"], text=True).splitlines())
if expected != actual:
    raise RuntimeError("toolchain differs from the reviewed lock: " + str({k: (v, actual.get(k)) for k,v in expected.items() if actual.get(k) != v}) + "; extras=" + str(sorted(actual.keys() - expected.keys())))
lock = json.loads((root / "tools/toolchain.lock.json").read_text())
if subprocess.check_output(["node", "--version"], text=True).strip() != "v" + lock["node"]:
    raise RuntimeError("Node version differs from tool lock")
print("Toolchain closure matches the reviewed lock")
