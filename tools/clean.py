"""Remove generated package outputs while retaining verification reports."""
import pathlib
import shutil

root=pathlib.Path(__file__).resolve().parents[1]
targets=[root/'_build',root/'node_modules']+list(root.glob('_build-*'))
cache=root/'.cache'
if cache.exists():
    targets.extend(p for p in cache.iterdir() if p.name != 'reports')
for path in targets:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)
    print('Cleaned',path.relative_to(root))
