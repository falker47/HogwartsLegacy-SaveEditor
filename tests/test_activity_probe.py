"""Read-only activity evidence; counters are not gameplay completion."""
from pathlib import Path
import importlib.util
import json
import sqlite3
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'inspect_activity_state.py'


def module():
    spec = importlib.util.spec_from_file_location('activity_probe', SCRIPT)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def database(secondary=False, minimal=False):
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE sentinel(value TEXT)')
        db.execute("INSERT INTO sentinel VALUES ('unchanged')")
        if not minimal:
            db.executescript("""
                CREATE TABLE SphinxPuzzleDynamic(SphinxPuzzleGUID TEXT, EInteractiveState INTEGER);
                CREATE TABLE EconomicExpiryDynamic(UniqueID TEXT, Expiry INTEGER);
                CREATE TABLE PlayerStatsDynamic(ActivityName TEXT, ActivityValue TEXT);
                CREATE TABLE AchievementDynamic(AchievementID TEXT);
                CREATE TABLE LocksDynamic(LockID TEXT);
                INSERT INTO EconomicExpiryDynamic VALUES ('butterfly-a',0),('unrelated-vendor',99);
                INSERT INTO PlayerStatsDynamic VALUES ('COM_11','Complete');
                INSERT INTO AchievementDynamic VALUES ('FGC_Complete_Merlin_001');
                INSERT INTO LocksDynamic VALUES ('FGC_Complete_Merlin_001');
            """)
            db.executemany('INSERT INTO SphinxPuzzleDynamic VALUES (?,?)',
                [('trial-a',2),('trial-c',34)] if secondary else [('trial-a',34),('trial-b',2)])
        return db.serialize()


CATALOG = [{'type':'Merlin','key':'trial-a'}, {'type':'Merlin','key':'trial-b'},
           {'type':'ButterflyChest','key':'butterfly-a'}, {'type':'ButterflyChest','key':'butterfly-b'}]


def test_pair_reports_raw_state_divergence_without_calling_it_completion():
    report = module().inspect_pair(database(), database(True), CATALOG)
    assert report['db1']['merlin']['state_counts'] == {'2':1,'34':1}
    assert report['db1']['butterfly']['catalog_keys_present'] == 1
    assert report['db1']['butterfly']['catalog_keys_missing'] == 1
    assert report['db1']['economic_expiry_total_rows'] == 2
    assert report['db1_db2_merlin_comparison'] == {
        'matching_keys':1, 'different_states':1, 'db1_only_keys':1, 'db2_only_keys':1}
    assert report['gameplay_completion_verified'] is False
    encoded = json.dumps(report)
    assert 'trial-a' not in encoded and 'unrelated-vendor' not in encoded


def test_no_catalog_never_counts_all_economic_rows_as_butterfly_chests():
    report = module().inspect_pair(database(), database())
    assert report['db1']['butterfly']['status'] == 'NEEDS_CATALOG'
    assert 'catalog_keys_present' not in report['db1']['butterfly']


def test_missing_tables_are_unavailable_instead_of_zero_completed():
    report = module().inspect_pair(database(minimal=True), database(minimal=True), CATALOG)
    assert report['db1']['merlin'] == {'status':'UNAVAILABLE'}
    assert report['db1']['butterfly'] == {'status':'UNAVAILABLE'}
    assert report['db1_db2_merlin_comparison'] == {'status':'UNAVAILABLE'}


def test_corrupt_database_is_an_error_instead_of_an_empty_progress_report():
    with pytest.raises(ValueError, match='SQLite'):
        module().inspect_pair(b'corrupt bytes', database())


def test_cli_only_reads_copies_and_emits_no_personal_keys_or_sidecars(tmp_path):
    db1, db2, catalog = [tmp_path / name for name in ('db1.sqlite','db2.sqlite','catalog.json')]
    db1.write_bytes(database())
    db2.write_bytes(database(True))
    catalog.write_text(json.dumps(CATALOG), encoding='utf8')
    before = {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in tmp_path.iterdir()}
    process = subprocess.run([sys.executable,str(SCRIPT),'--db1',str(db1),'--db2',str(db2),'--catalog',str(catalog)],capture_output=True,text=True)
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout)['gameplay_completion_verified'] is False
    assert {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in tmp_path.iterdir()} == before


@pytest.mark.parametrize('kind', ['text-state','null-state','missing-key','blank-key','duplicate-key'])
def test_unsupported_merlin_rows_never_echo_saved_text_or_hide_ambiguity(kind):
    data = database()
    with sqlite3.connect(':memory:') as db:
        db.deserialize(data)
        if kind == 'text-state':
            db.execute("UPDATE SphinxPuzzleDynamic SET EInteractiveState='PRIVATE_SENTINEL' WHERE SphinxPuzzleGUID='trial-a'")
        elif kind == 'null-state':
            db.execute("UPDATE SphinxPuzzleDynamic SET EInteractiveState=NULL WHERE SphinxPuzzleGUID='trial-a'")
        elif kind == 'missing-key':
            db.execute("UPDATE SphinxPuzzleDynamic SET SphinxPuzzleGUID=NULL WHERE SphinxPuzzleGUID='trial-a'")
        elif kind == 'blank-key':
            db.execute("UPDATE SphinxPuzzleDynamic SET SphinxPuzzleGUID=' ' WHERE SphinxPuzzleGUID='trial-a'")
        else:
            db.execute("INSERT INTO SphinxPuzzleDynamic VALUES ('TRIAL-A',2)")
        db.commit()
        data = db.serialize()
    report = module().inspect_pair(data, database(), CATALOG)
    assert report['db1']['merlin'] == {'status':'UNAVAILABLE'}
    assert report['db1_db2_merlin_comparison'] == {'status':'UNAVAILABLE'}
    assert 'PRIVATE_SENTINEL' not in json.dumps(report)


@pytest.mark.parametrize('catalog', [[],[{'type':'Merlin','key':'trial-a'}]])
def test_catalog_without_butterfly_keys_is_unavailable_evidence(catalog):
    report = module().inspect_pair(database(), database(), catalog)
    assert report['db1']['butterfly'] == {'status':'NEEDS_CATALOG'}
