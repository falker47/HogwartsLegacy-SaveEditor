"""Read-only Merlin/Butterfly evidence from standalone extracted DB copies.

No save writer or progression-completion recipe is provided. Database bytes are
deserialized in memory; this tool creates no database journals or output files.
"""
import argparse
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import sqlite3


def _rows(db, sql):
    try:
        return db.execute(sql).fetchall()
    except sqlite3.Error:
        return None  # Missing/unsupported table is not zero progress.


def _snapshot(data, catalog):
    if len(data) > 64 * 1024 * 1024 or not data.startswith(b'SQLite format 3\0'):
        raise ValueError('Invalid standalone SQLite copy')
    try:
        with closing(sqlite3.connect(':memory:')) as db:
            db.deserialize(data)
            db.execute('PRAGMA query_only = ON')
            if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                raise ValueError('Invalid standalone SQLite copy')
            rows = _rows(db, 'SELECT SphinxPuzzleGUID,EInteractiveState FROM SphinxPuzzleDynamic')
            # SQLite affinity does not enforce integer state values. Never
            # echo unsupported saved text, or silently collapse ambiguous keys.
            valid_merlin = rows is not None and all(
                isinstance(key, str) and key and key.strip() == key and key.isascii()
                and isinstance(state, int) for key, state in rows)
            merlin = {key.casefold():state for key,state in rows} if valid_merlin else None
            if merlin is not None and len(merlin) != len(rows):
                merlin = None
            merlin_report = {'status':'UNAVAILABLE'} if merlin is None else {
                'status':'READ_ONLY_EVIDENCE', 'rows':len(rows),
                'state_counts':dict(sorted(Counter(str(state) for _,state in rows).items()))}
            expiry = _rows(db, 'SELECT UniqueID,Expiry FROM EconomicExpiryDynamic')
            if expiry is None:
                butterfly = {'status':'UNAVAILABLE'}
            elif catalog is None:
                butterfly = {'status':'NEEDS_CATALOG'}
            else:
                keys = {row['key'].casefold() for row in catalog if row['type'] == 'ButterflyChest'}
                if not keys:
                    butterfly = {'status':'NEEDS_CATALOG'}
                else:
                    present = {str(key).casefold() for key,_ in expiry} & keys
                    butterfly = {'status':'READ_ONLY_EVIDENCE', 'catalog_keys':len(keys),
                        'catalog_keys_present':len(present), 'catalog_keys_missing':len(keys-present)}
            quest = _rows(db, "SELECT COUNT(*) FROM PlayerStatsDynamic WHERE ActivityName='COM_11' AND ActivityValue='Complete'")
            challenges = _rows(db, "SELECT COUNT(*) FROM AchievementDynamic WHERE AchievementID LIKE '%Merlin%'")
            locks = _rows(db, "SELECT COUNT(*) FROM LocksDynamic WHERE LockID LIKE '%Merlin%'")
            return {
                'merlin':merlin_report, 'butterfly':butterfly,
                'economic_expiry_total_rows':None if expiry is None else len(expiry),
                'COM_11_complete_marker_rows':None if quest is None else quest[0][0],
                'merlin_named_challenge_rows':None if challenges is None else challenges[0][0],
                'merlin_named_lock_rows':None if locks is None else locks[0][0]
            }, merlin
    except sqlite3.Error as exc:
        raise ValueError('Invalid standalone SQLite copy') from exc


def inspect_pair(db1: bytes, db2: bytes, catalog=None) -> dict:
    """Return anonymous counts; raw object states do not prove rewards/XP/events."""
    if catalog is not None:
        if not isinstance(catalog, list) or any(not isinstance(row, dict)
                or not isinstance(row.get('type'), str) or not isinstance(row.get('key'), str)
                for row in catalog):
            raise ValueError('Invalid collectible catalog')
    primary, primary_merlin = _snapshot(db1, catalog)
    secondary, secondary_merlin = _snapshot(db2, catalog)
    comparison = {'status':'UNAVAILABLE'}
    if primary_merlin is not None and secondary_merlin is not None:
        shared = primary_merlin.keys() & secondary_merlin.keys()
        comparison = {
            'matching_keys':len(shared),
            'different_states':sum(primary_merlin[key] != secondary_merlin[key] for key in shared),
            'db1_only_keys':len(primary_merlin.keys() - secondary_merlin.keys()),
            'db2_only_keys':len(secondary_merlin.keys() - primary_merlin.keys())
        }
    return {
        'gameplay_completion_verified':False,
        'interpretation':'Raw state/row-presence evidence only; discovery, collection, rewards, XP, challenges and achievements require controlled game observations.',
        'db1':primary, 'db2':secondary, 'db1_db2_merlin_comparison':comparison
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db1', type=Path, required=True, help='Standalone extracted DB1 copy')
    parser.add_argument('--db2', type=Path, required=True, help='Standalone extracted DB2 copy')
    parser.add_argument('--catalog', type=Path, help='Pinned Legilimens collectibles.json (optional)')
    args = parser.parse_args()
    try:
        catalog = json.loads(args.catalog.read_text(encoding='utf-8-sig')) if args.catalog else None
        report = inspect_pair(args.db1.read_bytes(), args.db2.read_bytes(), catalog)
    except (OSError, ValueError):
        parser.exit(1, 'Activity inspection failed: use valid standalone SQLite copies and collectible catalog.\n')
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
