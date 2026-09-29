"""Loose-save policy and read-only discovery/export of Game Pass WGS payloads."""

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Optional


MAX_WGS_PAYLOAD_SIZE = 50 * 1024 * 1024
HL_SAVE_TAG = re.compile(rb"(?<![A-Za-z0-9_-])HL-[0-9]{2}-[0-9]{2}(?![A-Za-z0-9_-])")

WGS_LIMITATION = (
    "Microsoft Store / Game Pass WGS containers cannot be edited in place. "
    "Use 'Export Game Pass Saves' for ordinary editable/migration copies. "
    "Changes to exported copies are NOT written back to WGS or Game Pass cloud storage. "
    "Do not rename or replace WGS files with this editor."
)


def find_hogwarts_wgs(local_app_data: str) -> Optional[Path]:
    """Check only the known title package; do not scan other games or payloads."""
    if not local_app_data:
        return None
    path = (Path(local_app_data) / "Packages" / "WarnerBros.Interactive.PHX_ktmk1xygcecda"
            / "SystemAppData" / "wgs")
    return path if path.is_dir() else None


def is_wgs_path(path: Path) -> bool:
    """Recognize WGS ancestors, including resolved junctions and copied containers.

    Metadata markers also protect a WGS user directory selected outside Packages.
    No file contents are read and no directories are created.
    """
    resolved = path.resolve()
    for parent in (resolved, *resolved.parents):
        if parent.name.casefold() == "wgs" and parent.parent.name.casefold() == "systemappdata":
            return True
        if (parent / "containers.index").is_file() or (parent / "container.index").is_file():
            return True
    return False


def require_loose_save_path(path: Path) -> None:
    if is_wgs_path(path):
        raise ValueError(WGS_LIMITATION)


def _plain_path(path: Path, *, directory: bool = False) -> bool:
    """Do not follow symbolic links or Windows junction/reparse points while scanning."""
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        return False
    return stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)


def find_wgs_user_directory(wgs_root: Path) -> Path:
    """Require exactly one immediate user folder with a containers.index marker."""
    if not wgs_root.is_dir():
        raise ValueError("Game Pass WGS root does not exist.")
    candidates = []
    for child in sorted(wgs_root.iterdir()):
        if not _plain_path(child, directory=True):
            continue
        marker = child / 'containers.index'
        if marker.exists() and _plain_path(marker):
            candidates.append(child)
    if not candidates:
        raise ValueError("No Game Pass WGS user folder with containers.index was found.")
    if len(candidates) != 1:
        raise ValueError("Multiple Game Pass WGS user folders were found; export is ambiguous.")
    return candidates[0]


def _read_wgs_payload(path: Path) -> bytes | None:
    """Bound both the size check and actual read, even if the source grows."""
    try:
        if not _plain_path(path):
            return None
        size = path.stat().st_size
        if not 0 < size <= MAX_WGS_PAYLOAD_SIZE:
            return None
        with path.open('rb') as source:
            data = source.read(MAX_WGS_PAYLOAD_SIZE + 1)
        return data if len(data) == size else None
    except OSError:
        return None


def _discover_wgs_payloads(wgs_root: Path) -> dict[str, tuple[Path, str]]:
    user = find_wgs_user_directory(wgs_root)
    found = {}
    # WGS layout is user/container/payload. Never recursively scan unrelated trees.
    for container in sorted(user.iterdir()):
        if not _plain_path(container, directory=True):
            continue
        for path in sorted(container.iterdir()):
            name = path.name.casefold()
            if name.endswith('.index') or name.startswith('container.'):
                continue
            data = _read_wgs_payload(path)
            if data is None:
                continue
            tags = set(HL_SAVE_TAG.findall(data))
            if len(tags) > 1:
                raise ValueError("A Game Pass payload contains multiple save identifiers; export is ambiguous.")
            if not tags:
                continue
            tag = tags.pop().decode('ascii')
            digest = hashlib.sha256(data).hexdigest()
            previous = found.get(tag)
            if previous is not None and previous[1] != digest:
                raise ValueError(f"Multiple different Game Pass payloads claim {tag}; export is ambiguous.")
            if previous is None:
                found[tag] = (path, digest)
    if not found:
        raise ValueError("No unambiguous Hogwarts Legacy Game Pass save payloads were found.")
    return dict(sorted(found.items()))


def discover_wgs_save_payloads(wgs_root: Path) -> dict[str, Path]:
    """Recognize bounded, unambiguous payloads and deduplicate identical contents."""
    return {tag: path for tag, (path, _) in _discover_wgs_payloads(wgs_root).items()}


def export_wgs_saves(wgs_root: Path, destination: Path) -> list[Path]:
    """Export byte-exact copies with exclusive creation and rollback; never write WGS."""
    root = wgs_root.resolve()
    destination = destination.resolve()
    require_loose_save_path(destination)
    if destination.is_relative_to(root):
        raise ValueError("Choose an export destination outside the Game Pass WGS source tree.")
    payloads = _discover_wgs_payloads(root)
    planned = [(source, digest, destination / f'{tag}.sav')
               for tag, (source, digest) in payloads.items()]
    existing = [target.name for _, _, target in planned if target.exists() or target.is_symlink()]
    if existing:
        raise ValueError(f"Destination already contains: {', '.join(existing)}. Choose a new folder.")
    destination.mkdir(parents=True, exist_ok=True)
    outputs = []
    created = {}
    try:
        for source, digest, target in planned:
            data = _read_wgs_payload(source)
            if data is None or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError("A Game Pass payload changed or became unreadable; retry export with the game closed.")
            require_loose_save_path(target)
            # 'xb' refuses files appearing after preflight. Track ownership BEFORE writing,
            # so a partially written current file is also removed on failure.
            with target.open('xb') as output:
                identity = os.fstat(output.fileno())
                created[target] = (identity.st_dev, identity.st_ino)
                outputs.append(target)
                output.write(data)
    except Exception as exc:
        cleanup_failed = []
        for target in outputs:
            try:
                identity = target.lstat()
                if (identity.st_dev, identity.st_ino) == created[target]:
                    target.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                cleanup_failed.append(target.name)
        if cleanup_failed:
            raise OSError(f"Export failed; could not remove partial outputs: {', '.join(cleanup_failed)}") from exc
        raise
    return outputs
