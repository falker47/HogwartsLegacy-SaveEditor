"""
Utility functions for Hogwarts Legacy Save Editor.
"""

import re
from typing import Dict

from .config import SAVE_FILE_PATTERN


def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes to a human-readable string.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Human-readable size string (e.g., "1.5 MB").
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def parse_save_filename(filename: str) -> Dict[str, str]:
    """
    Parse a Hogwarts Legacy save filename to extract slot and type info.
    
    Args:
        filename: The save filename (e.g., "HL-0-1.sav").
        
    Returns:
        Dictionary with 'slot', 'type', and 'display' keys.
    """
    info = {"slot": "Unknown", "type": "Save", "display": filename}
    match = re.match(SAVE_FILE_PATTERN, filename)
    if match:
        slot_num = int(match.group(1))
        save_type = int(match.group(2))
        info["type"] = "Manual Save" if save_type == 0 else f"Auto #{save_type}"
        info["slot"] = f"Slot {slot_num}"
        info["display"] = f"{info['slot']} - {info['type']}"
    return info
