"""Stage only redistributable assets; never bundle the developer's runtime folder."""
import argparse
from pathlib import Path
import shutil

PUBLIC_ASSETS = ('HLSGE.html', 'hlsaves.exe', 'editor_bridge.js')


def stage(source: Path, destination: Path) -> None:
    for name in PUBLIC_ASSETS:
        if not (source / name).is_file():
            raise FileNotFoundError(f'Missing release asset: {name}')
    destination.mkdir(parents=True, exist_ok=False)
    for name in PUBLIC_ASSETS:
        shutil.copyfile(source / name, destination / name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    stage(args.source, args.destination)
