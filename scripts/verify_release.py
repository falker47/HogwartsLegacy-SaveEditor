"""Verify the public package, including assets inside the PyInstaller executable."""
import argparse
import hashlib
import json
import runpy
from pathlib import Path
from PyInstaller.archive.readers import CArchiveReader

CONVERTER_SHA256 = '4080b409c125c29a3b977ed42160e36fb422fe0eaaa7f0c5d9419737a81cd3bb'
ASSETS = {'HLSGE.html', 'hlsaves.exe', 'editor_bridge.js'}


def verify(root, commit):
    required = {'HogwartsLegacy-SaveEditor.exe', 'LICENSE', 'CREDITS.md', 'THIRD_PARTY_NOTICES.md',
                'hlsavetool-LICENSE.txt', 'README.txt', 'READ-ME-FIRST.txt',
                'ACCEPTANCE.md', 'RELEASE-NOTES.md'} | {'assets/' + n for n in ASSETS}
    files = {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
    if not required <= files.keys():
        raise ValueError(f'Missing public files: {sorted(required - files.keys())}')
    def private(name):
        name = name.lower().replace('\\', '/')
        return ('oo2core' in name or name.endswith(('.sav', '.sqlite', '.db', '.bak'))
                or name.split('/')[-1] == 'config.json')
    if any(private(name) for name in files):
        raise ValueError('Private/runtime data found in public release')
    converter = files['assets/hlsaves.exe'].read_bytes()
    if hashlib.sha256(converter).hexdigest() != CONVERTER_SHA256:
        raise ValueError('Unvalidated converter in release')
    archive = CArchiveReader(str(files['HogwartsLegacy-SaveEditor.exe']))
    embedded = {n.replace('\\', '/'): n for n in archive.toc}
    if any(private(name) for name in embedded):
        raise ValueError('Private/runtime data embedded in executable')
    if {n for n in embedded if n.startswith('assets/')} != {'assets/' + n for n in ASSETS}:
        raise ValueError('Unexpected embedded assets')
    for name in ASSETS:
        if archive.extract(embedded['assets/' + name]) != files['assets/' + name].read_bytes():
            raise ValueError(f'Embedded/external asset mismatch: {name}')
    manifest = {'commit': commit, 'version': runpy.run_path(str(Path(__file__).resolve().parents[1] / 'src/config.py'))['VERSION'], 'embedded_assets_verified': True,
                'files': {n: {'size': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                          for n, p in sorted(files.items()) if n != 'RELEASE-MANIFEST.json'}}
    (root / 'RELEASE-MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'commit': commit, 'files': len(manifest['files']), 'embedded_assets_verified': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', required=True, type=Path)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    verify(args.release, args.commit)
