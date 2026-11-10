"""Put Pyodide and the kernel's extra wheel next to this file, so the built IDE loads nothing from a CDN.

Run in ide/ before `jupyter lite build`: python prepare.py

- static/pyodide/: the Pyodide core (interpreter and standard library) plus only the wheels the kernel needs
  to start: micropip, ipython, jedi and what they depend on. The lock file lists only those, so importing a
  package that is not here fails with ModuleNotFoundError instead of a download.
- pypi/: comm, which ipykernel needs and Pyodide does not ship. piplite serves it, and jupyter-lite.json turns
  off the fallback to PyPI.

Everything is pinned and checked by sha256. Downloads are kept in .cache/ for the next run.
"""
import hashlib
import io
import json
import shutil
import tarfile
import urllib.request
from pathlib import Path

PYODIDE = '314.0.6'  # the version jupyterlite-pyodide-kernel 0.8.7 is built for
CORE = (f'https://github.com/pyodide/pyodide/releases/download/{PYODIDE}/pyodide-core-{PYODIDE}.tar.bz2',
        '1016c31e39ce3764d9a418cbb491a392c802c1b86ccc1367f009f5c59bf8f5fd')
CORE_FILES = ['pyodide.js', 'pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm', 'python_stdlib.zip', 'package.json']
WHEELS = f'https://cdn.jsdelivr.net/pyodide/v{PYODIDE}/full/'  # used only here, while building
ROOTS = ['micropip', 'ipython', 'jedi']  # what the kernel loads when it starts, found by watching a real start
EXTRA = [('https://files.pythonhosted.org/packages/60/97/891a0971e1e4a8c5d2b20bbe0e524dc04548d2307fee33cdeba148fd4fc7/'
          'comm-0.2.3-py3-none-any.whl', 'c615d91d75f7f04f095b30d1c1711babd43bdc6419c1be9886a85f2f4e489417')]

HERE = Path(__file__).resolve().parent
CACHE = HERE / '.cache'


def fetch(url, sha256):
    """The bytes at url, from the cache when they are already there; stops if the hash is not the pinned one."""
    path = CACHE / url.rsplit('/', 1)[1]
    if not path.exists():
        CACHE.mkdir(exist_ok=True)
        with urllib.request.urlopen(url, timeout=120) as response:
            path.write_bytes(response.read())
    data = path.read_bytes()
    found = hashlib.sha256(data).hexdigest()
    assert found == sha256, f'{url}: sha256 {found}, expected {sha256}'
    return data


def name(text):
    return text.lower().replace('_', '-')


def main():
    out = HERE / 'static' / 'pyodide'
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(fetch(*CORE)), mode='r:bz2') as tar:
        for file in CORE_FILES:
            (out / file).write_bytes(tar.extractfile(f'pyodide/{file}').read())
        lock = json.load(tar.extractfile('pyodide/pyodide-lock.json'))

    packages = {name(key): value for key, value in lock['packages'].items()}
    keep, todo = {}, list(ROOTS)
    while todo:
        key = name(todo.pop())
        if key not in keep:
            keep[key] = packages[key]
            todo += packages[key]['depends']
    for package in keep.values():
        (out / package['file_name']).write_bytes(fetch(WHEELS + package['file_name'], package['sha256']))
    lock['packages'] = {key: value for key, value in lock['packages'].items() if name(key) in keep}
    (out / 'pyodide-lock.json').write_text(json.dumps(lock, indent=1) + '\n')

    wheels = HERE / 'pypi'
    shutil.rmtree(wheels, ignore_errors=True)
    wheels.mkdir()
    for url, sha256 in EXTRA:
        (wheels / url.rsplit('/', 1)[1]).write_bytes(fetch(url, sha256))
    size = sum(p.stat().st_size for p in out.rglob('*')) >> 20
    print(f'Pyodide {PYODIDE}: {len(CORE_FILES)} core files and {len(keep)} wheels ({size} MB); {len(EXTRA)} wheel for piplite')


if __name__ == '__main__':
    main()
