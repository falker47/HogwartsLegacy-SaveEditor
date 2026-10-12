"""Verified exclusive writes for disposable exports and immutable backup copies."""

import os
from pathlib import Path

from .save_paths import require_loose_save_path


def write_new_verified(destination: Path, data: bytes) -> None:
    """Never overwrite; detect short writes and clean up only our own output."""
    require_loose_save_path(destination)
    identity = None
    try:
        with destination.open('xb') as output:
            info = os.fstat(output.fileno())
            identity = (info.st_dev, info.st_ino)
            if output.write(data) != len(data):
                raise OSError('Incomplete file write')
            output.flush()
            os.fsync(output.fileno())
        if destination.read_bytes() != data:
            raise OSError('File verification failed')
    except BaseException as exc:
        if identity is not None:
            try:
                info = destination.lstat()
                if (info.st_dev, info.st_ino) == identity:
                    destination.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup:
                raise OSError(f'Write failed; could not remove partial file: {destination}: {cleanup}') from exc
        raise
