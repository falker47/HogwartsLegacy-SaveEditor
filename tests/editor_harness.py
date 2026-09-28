"""JSON boundary for Node tests: real EditorApi/files, mocked desktop and hlsaves.

All data is synthetic. The minimal GVAS-shaped container exercises extraction;
it is not a game fixture or evidence of in-game compatibility.
"""

import base64
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import struct
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.editor import EditorApi, get_editor_bridge_js  # noqa: E402


def make_databases(root):
    payloads = []
    for index in (1, 2):
        path = root / f"fixture{index}.sqlite"
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE identity(value TEXT)")
            db.execute("INSERT INTO identity VALUES (?)", (f"database-{index}",))
            db.execute("CREATE TABLE CollectionDynamic(CategoryID TEXT)")
            db.execute("CREATE TABLE MiscDataDynamic(DataName TEXT, DataValue TEXT)")
            db.execute("INSERT INTO MiscDataDynamic VALUES ('PerkPoints', '3')")
        payloads.append(path.read_bytes())
    return payloads


def synthetic_save(payloads):
    data = bytearray(b"GVAS" + bytes(32))
    for marker, payload in zip((b"RawDatabaseImage", b"RawExclusiveImage"), payloads):
        data.extend(marker + bytes(32) + b"ByteProperty" + bytes(2))
        data.extend(struct.pack("<i", len(payload)) + payload)
    return bytes(data)


def inspect_files(root):
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            info = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            if path.suffix == ".sqlite":
                with closing(sqlite3.connect(path)) as db:
                    info["integrity"] = db.execute("PRAGMA integrity_check").fetchone()[0]
                    info["identity"] = db.execute("SELECT value FROM identity").fetchone()[0]
            result[str(path.relative_to(root))] = info
    return result


def invoke(root, request):
    window = Mock()
    status = Mock()
    window.create_file_dialog.return_value = request.get("destination")
    api = EditorApi(str(root / "loaded.dat"), "loaded.dat", str(root / "original.sav"),
                    "mock-hlsaves", str(root), status)
    api.set_window(window)
    process = SimpleNamespace(returncode=request.get("returncode", 0), stderr="mock compression error")
    with patch.dict(sys.modules, {"webview": SimpleNamespace(SAVE_DIALOG=30)}), \
            patch("src.editor.subprocess.run", return_value=process) as run:
        result = getattr(api, request["method"])(*request.get("args", []))
    return {"result": result, "subprocess": [call.args[0] for call in run.call_args_list],
            "status": [call.args for call in status.call_args_list],
            "closed": window.destroy.call_count,
            "dialogs": [{"args": call.args, "kwargs": call.kwargs}
                        for call in window.create_file_dialog.call_args_list]}


def main(request):
    root = Path(request["root"])
    if request["op"] == "fixture":
        payloads = make_databases(root)
        save = synthetic_save(payloads)
        (root / "loaded.dat").write_bytes(save)
        (root / "original.sav").write_bytes(b"original sentinel: never overwrite")
        (root / "Backups").mkdir()
        (root / "Backups" / "original.sav").write_bytes(b"backup sentinel")
        repo = Path(__file__).resolve().parents[1]
        return {"payloads": [base64.b64encode(p).decode() for p in payloads],
                "save": base64.b64encode(save).decode(),
                "bridges": {"external": get_editor_bridge_js(str(repo)),
                            "fallback": get_editor_bridge_js(str(root))},
                "files": inspect_files(root)}
    if request["op"] == "inspect":
        return inspect_files(root)
    return invoke(root, request)


if __name__ == "__main__":
    print(json.dumps(main(json.load(sys.stdin))))
