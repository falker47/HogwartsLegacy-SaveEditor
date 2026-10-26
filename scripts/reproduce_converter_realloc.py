"""Generate synthetic databases and exercise a pinned native converter without user saves."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import struct
import subprocess

PINNED_SHA256 = "bdf28ae18dc5ecf049af37ca863085851f2cd0f5b22895f9637c5820c8d0f70e"


def fstring(value):
    encoded = value.encode("ascii") + b"\0"
    return struct.pack("<i", len(encoded)) + encoded


def fixture_bytes():
    images = []
    for size in (36000, 100):
        with sqlite3.connect(":memory:") as db:
            db.execute("CREATE TABLE synthetic(value BLOB)")
            db.execute("INSERT INTO synthetic VALUES (zeroblob(?))", (size,))
            db.commit()
            assert db.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
            images.append(db.serialize())
    header = (b"GVAS" + struct.pack("<iiHHHI", 2, 524, 4, 27, 2, 123)
              + fstring("synthetic") + struct.pack("<ii", 3, 0)
              + fstring("/Script/PersistentData.PersistentGameData"))
    result = bytearray(header)
    for name, image in zip(("RawDatabaseImage", "RawExclusiveImage"), images):
        payload = struct.pack("<i", len(image)) + image
        result += (fstring(name) + fstring("ArrayProperty")
                   + struct.pack("<ii", len(payload), 0) + fstring("ByteProperty") + b"\0" + payload)
    return bytes(result) + fstring("None") + bytes(4)


def reproduce(converter, out_dir, expected_sha256):
    converter = Path(converter).resolve(strict=True)
    if hashlib.sha256(converter.read_bytes()).hexdigest() != expected_sha256.lower():
        raise ValueError("Converter SHA256 mismatch; no native code executed")
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=False)
    source, candidate, verified = (out_dir / name for name in
                                    ("synthetic.decomp", "candidate.sav", "verified.decomp"))
    payload = fixture_bytes()
    with source.open("xb") as output:
        output.write(payload)
    result = {"converter_sha256": expected_sha256.lower(),
              "input_sha256": hashlib.sha256(payload).hexdigest(), "stages": []}
    for mode, input_path, output_path in (("-c", source, candidate), ("-d", candidate, verified)):
        completed = subprocess.run([str(converter), mode, str(input_path), str(output_path), "-v"],
                                   cwd=converter.parent, stdin=subprocess.DEVNULL,
                                   capture_output=True, text=True, errors="replace", timeout=60)
        diagnostic = completed.stdout + completed.stderr
        for path, label in ((out_dir, "<synthetic-dir>"), (converter.parent, "<runtime-dir>")):
            diagnostic = diagnostic.replace(str(path), label)
        result["stages"].append({"mode": mode, "exit_code": completed.returncode,
                                 "diagnostic": diagnostic})
        if completed.returncode != 0 or not output_path.is_file():
            break
    result["exact_roundtrip"] = verified.is_file() and verified.read_bytes() == payload
    result["source_unchanged"] = source.read_bytes() == payload
    (out_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--converter", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path,
                        help="New directory only; an existing directory is rejected")
    parser.add_argument("--expected-sha256", default=PINNED_SHA256)
    args = parser.parse_args()
    result = reproduce(args.converter, args.out_dir, args.expected_sha256)
    print(json.dumps({key: value for key, value in result.items() if key != "stages"}))
    success = (result["exact_roundtrip"] and result["source_unchanged"]
               and len(result["stages"]) == 2
               and all(stage["exit_code"] == 0 for stage in result["stages"]))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
