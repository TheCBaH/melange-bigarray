import hashlib
import json
import pathlib
import urllib.request

root = pathlib.Path(__file__).resolve().parents[1]
for entry in json.loads((root / "tools/oracles.lock.json").read_text()):
    repo = entry.get("repo", "ocaml/ocaml").replace("/", "-")
    target = root / ".cache/oracles" / repo / entry["version"] / entry["path"]
    if target.exists():
        data = target.read_bytes()
    else:
        data = urllib.request.urlopen(entry["url"], timeout=60).read()
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise RuntimeError("oracle source checksum mismatch: " + entry["url"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
print("All 23 oracle/compiler sources verified")
