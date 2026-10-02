import json
import os
import pathlib
import shutil
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[1]
version = subprocess.check_output(['ocamlc', '-version'], text=True).strip()
work = root / '.cache/traces' / version
reports = root / '.cache/reports' / version
reports.mkdir(parents=True, exist_ok=True)
half = version.startswith('5.')
count = int(os.environ.get('TRACE_COUNT', '1000'))
if not 1000 <= count <= 100000:
    raise RuntimeError('trace count must be between 1000 and 100000')
mode = sys.argv[1]

def command(args, **kwargs):
    subprocess.run(args, check=True, timeout=600, **kwargs)

def run_report(name, args):
    out = reports / (name + '.tsv')
    err = reports / (name + '.stderr')
    with out.open('w') as stdout, err.open('w') as stderr:
        subprocess.run(args, stdout=stdout, stderr=stderr, check=True, timeout=120)
    if out.stat().st_size > 16 * 1024 * 1024:
        raise RuntimeError('trace payload exceeds 16 MiB')
    return out

if mode == 'build':
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    prefix = work / 'installed'
    command(['dune', 'build', '--build-dir', os.environ.get('BUILD_DIR', '_build-'+version), '@install'])
    command(['dune', 'install', '--build-dir', os.environ.get('BUILD_DIR', '_build-'+version), '--prefix', str(prefix)])
    source = (root / 'test/trace.ml.in').read_text()
    source = source.replace('(* FLOAT16_KIND *)', 'K ("float16", B.float16, (fun n -> float n /. 7.), fbits);' if half else '')
    tests = '''
  let a = B.Array1.create B.float16 B.c_layout 1 in
  for bits = 0 to 65535 do
    Backend.half_poke a bits;
    emit ("half/decode/" ^ string_of_int bits) (fbits (B.Array1.get a 0))
  done;
  List.iteri (fun i value ->
    B.Array1.set a 0 value;
    emit ("half/write/" ^ string_of_int i) (fbits (B.Array1.get a 0)))
    [0.; -0.; infinity; neg_infinity; nan; 65504.; 65519.99999958789;
     65520.; -65520.; 0.00006103515625; 0.000000059604644775390625;
     0.0000000298023223876953125; 1.00048828125; 1.00146484375];
'''
    source = source.replace('(* FLOAT16_TESTS *)', tests if half else '')
    for backend in ['native', 'jsoo', 'melange']:
        path = work / backend
        path.mkdir()
        (path / 'trace.ml').write_text(source)
        (path / 'multidimensional.ml').write_text((root / 'test/multidimensional.ml.in').read_text())
        (path / 'ops.ml').write_text((root / 'test/ops.ml.in').read_text())
        (path / 'dune-project').write_text('(lang dune 3.21)\n(using melange 1.0)\n')
        header = 'module Bigarray = ' + ('Melange_bigarray' if backend == 'melange' else 'Bigarray') + '\n'
        header += 'module Nativeint = ' + ('Melange_bigarray.Nativeint' if backend == 'melange' else 'Nativeint') + '\n'
        header += 'let trace_count = ' + str(count) + '\n'
        if backend == 'melange':
            header += 'module Ops = Melange_bigarray.Ops\n'
        else:
            header += """module Ops = struct
 type packed = P : ('a,'b,'c) Bigarray.Genarray.t -> packed
 let compare a b = Stdlib.compare (P a) (P b)
 let equal a b = P a = P b
 let hash a = Hashtbl.hash (P a)
 let seeded_hash seed a = Hashtbl.seeded_hash seed (P a)
end
"""
        if half:
            ty = '(float, Bigarray.float16_elt, Bigarray.c_layout) Bigarray.Array1.t'
            if backend == 'melange':
                header += 'let half_poke : ' + ty + ' -> int -> unit = [%mel.raw {|function(a, bits) { a.data[a.offset] = bits; }|}]\n'
            else:
                header += 'external half_poke : ' + ty + ' -> int -> unit = "oracle_half_poke"\n'
        if backend == 'melange':
            header += """let raw_bytes : 'a Bigarray.Array1.t -> int array = [%mel.raw {|function(a) { return Array.from(new Uint8Array(a.data.buffer, a.data.byteOffset + a.offset*8, a.count*8)); }|}]
""".replace("'a Bigarray.Array1.t", "(float,Bigarray.float64_elt,Bigarray.c_layout) Bigarray.Array1.t")
            header += """let poison : (float,Bigarray.float64_elt,Bigarray.c_layout) Bigarray.Array1.t -> unit = [%mel.raw {|function(a) { const bytes = new Uint8Array(a.data.buffer, a.data.byteOffset, 16); bytes.set([0x34,0x12,0,0,0,0,0xf0,0x7f,0,0,0,0,0,0,0,0x80]); }|}]
let boundaries () =
 let open Bigarray in
 let reject f = try f (); failwith "overflow accepted" with Invalid_argument _ -> () in
 reject (fun () -> ignore (Genarray.create char c_layout (Array.make 17 1)));
 reject (fun () -> ignore (Genarray.create char c_layout [|0;-1|]));
 reject (fun () -> ignore (Genarray.create char c_layout [|65536;65536|]));
 reject (fun () -> ignore (Array1.create char c_layout 0x40000000));
 reject (fun () -> ignore (Array1.create int64 c_layout 0x7fffffff));
 let empty = Genarray.create char c_layout [|0x7fffffff;0x7fffffff;0|] in
 assert (Genarray.size_in_bytes empty = 0);
 let scalar = Genarray.create char c_layout [||] in
 assert (Genarray.size_in_bytes scalar = 1);
 reject (fun () -> ignore (reshape scalar [|65536;65536|]));
 let zero = Genarray.create char c_layout [|0|] in
 reject (fun () -> ignore (reshape zero [|65536;65536;65536;65536|]));
 let empty_f = Genarray.create char fortran_layout [|0;0x7fffffff|] in
 reject (fun () -> ignore (Genarray.sub_right empty_f min_int 0));
 reject (fun () -> ignore (Genarray.get empty [|0x7ffffffe;0x7ffffffe;0|]));
 let rank16 = Genarray.create char c_layout (Array.make 16 1) in
 Genarray.set rank16 (Array.make 16 0) 'x';
 assert (Genarray.get rank16 (Array.make 16 0) = 'x');
 let a = Array1.create float64 c_layout 2 in
 let b = Array1.create float64 c_layout 2 in
 poison a; Array1.blit a b;
 assert (raw_bytes a = raw_bytes b);
 let before = Array.sub (raw_bytes a) 0 8 in
 Array1.fill (Array1.sub a 1 1) 7.;
 assert (Array.sub (raw_bytes a) 0 8 = before)

"""
        else:
            header += 'let boundaries () = ()\n'
        (path / 'backend.ml').write_text(header)
        if backend == 'native':
            dune = '(executable (name trace) (modules trace backend multidimensional ops) (modes exe)'
            if half:
                dune += ' (foreign_stubs (language c) (names half_poke))'
                (path / 'half_poke.c').write_text('''#include <stdint.h>
#include <caml/mlvalues.h>
#include <caml/bigarray.h>
CAMLprim value oracle_half_poke(value a, value bits) {
  ((uint16_t *)Caml_ba_data_val(a))[0] = (uint16_t)Long_val(bits);
  return Val_unit;
}
''')
            dune += ')\n'
        elif backend == 'jsoo':
            dune = '(executable (name trace) (modules trace backend multidimensional ops) (modes js) (js_of_ocaml (javascript_files oracle.js)))\n'
            (path / 'oracle.js').write_text('//Provides: oracle_half_poke\nfunction oracle_half_poke(a, bits) { a.data[0] = bits; return 0; }\n')
        else:
            dune = '(melange.emit (target output) (modules trace backend multidimensional ops) (libraries melange-bigarray) (preprocess (pps melange.ppx)))\n'
        (path / 'dune').write_text(dune)
        env = dict(os.environ, OCAMLPATH=str(prefix / 'lib'))
        command(['dune', 'build', '--root', str(path), '@all'], env=env)
    (work / 'configuration.json').write_text(json.dumps({'count': count, 'ocaml': version, 'half': half})+'\n')
elif mode == 'node':
    run_report('native', [str(work / 'native/_build/default/trace.exe')])
    run_report('jsoo-node', ['node', '--max-old-space-size=256', str(work / 'jsoo/_build/default/trace.bc.js')])
    run_report('melange-node', ['node', '--max-old-space-size=256', str(work / 'melange/_build/default/output/trace.js')])
elif mode == 'compare':
    files = ['native', 'jsoo-node', 'melange-node', 'jsoo-chromium', 'melange-chromium']
    reference = (reports / 'native.tsv').read_text().splitlines()
    for backend in files[1:]:
        actual = (reports / (backend + '.tsv')).read_text().splitlines()
        if actual != reference:
            for i, (a,b) in enumerate(zip(reference,actual)):
                if a != b:
                    (reports / 'failure.json').write_text(json.dumps({'backend': backend, 'line': i, 'native': a, 'actual': b, 'seed': '13579bdf', 'count': count},indent=2)+'\n')
                    raise RuntimeError(f'{backend}: first mismatch at {i}: {a!r} != {b!r}')
            raise RuntimeError(backend + ': report length mismatch')
    report = json.loads((work / 'configuration.json').read_text())
    report.update({'source': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
                   'dirty': bool(subprocess.check_output(['git','status','--porcelain'], text=True)),
                   'runtimes': files, 'seed': '13579bdf', 'observations': len(reference), 'byte_limit': '0x3fffffff'})
    (reports / 'differential.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
else:
    raise RuntimeError('unknown trace action')
