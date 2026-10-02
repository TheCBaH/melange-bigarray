import hashlib
import json
import pathlib
import urllib.request

root = pathlib.Path(__file__).resolve().parents[1]
entries = json.loads((root / "tools/oracles.lock.json").read_text())
for entry in entries:
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
print(f"All {len(entries)} oracle/compiler/client sources verified")
