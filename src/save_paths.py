"""Save location policy. WGS containers are detected, never edited as loose files."""

from pathlib import Path
from typing import Optional


WGS_LIMITATION = (
    "Microsoft Store / Game Pass (WGS) saves are not supported for import or editing. "
    "Their container metadata and cloud synchronization require a separate workflow. "
    "Do not rename or replace WGS files with this editor. "
    "Browse remains available for ordinary Steam/Epic .sav folders."
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
