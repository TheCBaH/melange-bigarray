import pathlib
import sys

half = int(sys.argv[1].split(".")[0]) >= 5
for suffix in ["ml", "mli"]:
    s = pathlib.Path("melange_bigarray." + suffix + ".in").read_text()
    if half:
        s = s.replace("type float32_elt", "type float16_elt = Float16_elt\ntype float32_elt", 1)
        s = s.replace(" | Float32", " | Float16 : (float, float16_elt) kind\n | Float32", 1)
        if suffix == "ml":
            s = s.replace("let float64", "let float16 = Float16\nlet float64", 1)
            s = s.replace("| Float32 ->", "| Float16 -> 0.\n      | Float32 ->", 1)
        else:
            s = s.replace("val float64", "val float16 : (float,float16_elt) kind\nval float64", 1)
    pathlib.Path("melange_bigarray." + suffix).write_text(s)
