import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parents[1]
version = sys.argv[1]
half = int(version.split('.')[0]) >= 5
api_version = '4.14.4' if not half else '5.2.1' if version.startswith('5.2.') else '5.3.0'
api = (root / 'api' / (api_version + '.mli')).read_text()
types = api[:api.index('val float')]
layouts = api[api.index('type c_layout'):api.index('module Genarray')]
layouts = re.sub(r'val\s+\w+\s*:[^\n]*', '', layouts)
constructors = re.findall(r'\| (\w+)\s*:', types)
values = '\n'.join('let ' + c.lower() + ' = ' + c for c in constructors)
values += '\nlet c_layout = C_layout\nlet fortran_layout = Fortran_layout\n'
s = pathlib.Path('melange_bigarray.ml.in').read_text().replace('(* TYPES *)', types + layouts + values)
for marker, code in {
 'CODE': '| Float16 -> 13',
 'READ': '| Float16 -> half_decode (load t.data i)',
 'WRITE': '| Float16 -> store t.data i (half_encode value)',
}.items():
    s = s.replace('(* FLOAT16_' + marker + ' *)', code if half else '')
if not half:
    s = re.sub(r'let half_decode[\s\S]*?(?=let kind_code)', '', s)
pathlib.Path('melange_bigarray.ml').write_text(s)
iface = re.sub(r'external(\s+\w+\s*:[\s\S]*?)=\s*"[^"]*"', r'val\1', api)
iface += '''\nmodule Nativeint : sig
 val of_int : int -> nativeint
 val to_int : nativeint -> int
 val of_int32 : int32 -> nativeint
 val to_int32 : nativeint -> int32
 val add : nativeint -> nativeint -> nativeint
 val sub : nativeint -> nativeint -> nativeint
 val mul : nativeint -> nativeint -> nativeint
 val neg : nativeint -> nativeint
 val compare : nativeint -> nativeint -> int
 val equal : nativeint -> nativeint -> bool
 val of_string : string -> nativeint
 val to_string : nativeint -> string
end
'''
pathlib.Path('melange_bigarray.mli').write_text(iface)
