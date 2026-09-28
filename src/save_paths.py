"""Save location policy and safe Game Pass/WGS export support."""

from pathlib import Path
import hashlib
import re
import shutil
from typing import Dict, Optional


MAX_WGS_PAYLOAD_SIZE = 50 * 1024 * 1024
HL_SAVE_TAG = re.compile(rb"HL-\d{2}-\d{2}")

WGS_LIMITATION = (
    "Microsoft Store / Game Pass WGS containers are not supported for in-place editing "
    "or write-back. Their container metadata and cloud synchronization require the WGS "
    "storage protocol. Use 'Export Game Pass Saves' to copy recognized payloads to "
    "ordinary .sav files without modifying WGS, then edit/migrate those exported copies."
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


def find_wgs_user_directory(wgs_root: Path) -> Path:
    """Resolve exactly one WGS user directory by its containers.index marker."""
    if not wgs_root.is_dir():
        raise ValueError("Game Pass WGS root does not exist.")
    candidates = sorted(
        child for child in wgs_root.iterdir()
        if child.is_dir() and (child / "containers.index").is_file()
    )
    if not candidates:
        raise ValueError("No Game Pass WGS user folder with containers.index was found.")
    if len(candidates) > 1:
        raise ValueError("Multiple Game Pass WGS user folders were found; export is ambiguous.")
    return candidates[0]


def _payload_tag(path: Path) -> tuple[str, str] | None:
    """Return (HL tag, sha256) for one unambiguous bounded WGS payload."""
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size <= 0 or size > MAX_WGS_PAYLOAD_SIZE:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    tags = {match.decode("ascii") for match in HL_SAVE_TAG.findall(data)}
    if len(tags) != 1:
        return None
    return next(iter(tags)), hashlib.sha256(data).hexdigest()


def discover_wgs_save_payloads(wgs_root: Path) -> Dict[str, Path]:
    """Find unambiguous WGS payloads containing one internal HL-XX-XX save tag.

    The WGS source is read-only. Duplicate byte-identical payloads are deduplicated.
    Conflicting payloads for the same save tag fail closed.
    """
    user_dir = find_wgs_user_directory(wgs_root)
    found: Dict[str, tuple[Path, str]] = {}
    for path in sorted(user_dir.rglob("*")):
        if not path.is_file() or path.name.casefold().endswith(".index"):
            continue
        tagged = _payload_tag(path)
        if tagged is None:
            continue
        tag, digest = tagged
        previous = found.get(tag)
        if previous and previous[1] != digest:
            raise ValueError(
                f"Multiple different Game Pass payloads claim {tag}; export is ambiguous."
            )
        if previous is None:
            found[tag] = (path, digest)

    if not found:
        raise ValueError("No unambiguous Hogwarts Legacy Game Pass save payloads were found.")
    return {tag: path for tag, (path, _) in sorted(found.items())}


def export_wgs_saves(wgs_root: Path, destination: Path) -> list[Path]:
    """Copy recognized WGS payloads to ordinary .sav files without touching WGS."""
    require_loose_save_path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    payloads = discover_wgs_save_payloads(wgs_root)
    planned = [(source, destination / f"{tag}.sav") for tag, source in payloads.items()]
    existing = [target for _, target in planned if target.exists()]
    if existing:
        names = ", ".join(target.name for target in existing)
        raise ValueError(f"Destination already contains: {names}. Choose an empty/new folder.")

    outputs: list[Path] = []
    try:
        for source, target in planned:
            shutil.copy2(source, target)
            outputs.append(target)
    except Exception:
        for target in outputs:
            target.unlink(missing_ok=True)
        raise
    return outputs
