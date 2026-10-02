import json
import os
import pathlib
import shutil
import subprocess

root = pathlib.Path.cwd()
version = subprocess.check_output(['ocamlc', '-version'], text=True).strip()
reports = root / '.cache/reports' / version
reports.mkdir(parents=True, exist_ok=True)
work = root / ".cache/spike" / version
if work.exists():
    shutil.rmtree(work)
work.mkdir(parents=True)
prefix = work / "installed"
subprocess.run(["dune", "build", "--build-dir", os.environ.get("BUILD_DIR", "_build-"+version), "@install"], check=True)
subprocess.run(["dune", "install", "--build-dir", os.environ.get("BUILD_DIR", "_build-"+version), "--prefix", str(prefix)], check=True)
env = dict(os.environ, OCAMLPATH=str(prefix / "lib"))
results = []

def client(name, modules, libraries, expected=None):
    path = work / name
    path.mkdir()
    (path / "dune-project").write_text("(lang dune 3.21)\n(using melange 1.0)\n")
    (path / "dune").write_text("(melange.emit (target output) (libraries " + libraries + "))\n")
    for filename, source in modules.items():
        (path / filename).write_text(source)
    r = subprocess.run(["dune", "build", "--root", str(path), "@all"], env=env,
                       text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (reports / (name + ".log")).write_text(r.stdout)
    if expected:
        if r.returncode == 0 or expected not in r.stdout:
            raise RuntimeError(name + ": unexpected negative-client result: " + r.stdout)
    else:
        if r.returncode:
            raise RuntimeError(name + ": " + r.stdout)
        subprocess.run(["node", str(path / "_build/default/output/probe.js")], check=True)
    results.append({"client": name, "expected_failure": expected, "result": "passed"})

client("wrapped", {"probe.ml": (root / "spike/probe.ml").read_text(),
                   "separate.ml": (root / "spike/separate.ml").read_text()}, "melange-bigarray")
client("compat", {"probe.ml": "let () = let a = Bigarray.Array1.create Bigarray.float64 Bigarray.c_layout 1 in a.{0} <- 7.; assert (a.{0} = 7.)\n"}, "melange-bigarray.compat")
client("char-phantom", {"probe.ml": "let _ : (char, Melange_bigarray.int8_unsigned_elt, Melange_bigarray.c_layout) Melange_bigarray.Array1.t = Melange_bigarray.Array1.create Melange_bigarray.char Melange_bigarray.c_layout 1\n"}, "melange-bigarray")
client("wrong-element", {"probe.ml": "let a = Melange_bigarray.Array1.create Melange_bigarray.float64 Melange_bigarray.c_layout 1\nlet () = Melange_bigarray.Array1.set a 0 1\n"}, "melange-bigarray", "int")
client("provider-mismatch", {"probe.ml": "let a = Melange_bigarray.Array1.create Melange_bigarray.float64 Melange_bigarray.c_layout 1\nlet _ = Stdlib.Bigarray.Array1.get a 0\n"}, "melange-bigarray", "Unbound module Stdlib.Bigarray")
client("native-primitive", {"probe.ml": 'external get : \'a -> int -> float = "%caml_ba_ref_1"\nlet read a = get a 0\n'}, "melange-bigarray", "Unknown builtin primitive")
client("hidden-storage", {"probe.ml": "let read a = a.Melange_bigarray.Genarray.data\n"}, "melange-bigarray", "Unbound record field")
client("nativeint-literal", {"probe.ml": "let _ = 1n\n"}, "melange-bigarray", "nativeint")
client("injective", {"probe.ml": "module B = Melange_bigarray\ntype (_,_) eq = Refl : ('a,'a) eq\nlet inject : type a b k l. ((a,k,l) B.Array1.t,(b,k,l) B.Array1.t) eq -> (a,b) eq = function Refl -> Refl\n"}, "melange-bigarray")
client("wrong-layout", {"probe.ml": "module B = Melange_bigarray\nlet a = B.Array1.create B.float64 B.c_layout 1\nlet _ : (float,B.float64_elt,B.fortran_layout) B.Array1.t = a\n"}, "melange-bigarray", "c_layout")
version = subprocess.check_output(["ocamlc", "-version"], text=True).strip()
client("float16-selection", {"probe.ml": "let _ = Melange_bigarray.Float16\n"}, "melange-bigarray", "Unbound constructor" if version.startswith("4.") else None)
report = {"source": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
          "ocaml": subprocess.check_output(["ocamlc", "-version"], text=True).strip(),
          "melange": subprocess.check_output(["opam", "show", "melange", "--field=installed-version"], text=True).strip(),
          "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True)),
          "node": subprocess.check_output(["node", "--version"], text=True).strip(), "clients": results}
(reports / "spike.json").write_text(json.dumps(report, indent=2) + "\n")
(reports / "opam-packages.txt").write_text(subprocess.check_output(["opam", "list", "--installed", "--columns=name,version", "--short"], text=True))
print(json.dumps(report, indent=2))
