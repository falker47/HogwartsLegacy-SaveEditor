const assert = require('node:assert/strict');
const { test } = require('node:test');
const { readFileSync, existsSync } = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
const { parse } = require('@vue/compiler-sfc');
const initSqlJs = require('sql.js');

// Execute production TS and Vue setup code. SQL, dirty-field computation and
// manager logic are real; only page mounting and application state are supplied.
function loader(state) {
    const cache = new Map();
    function load(relative) {
        const file = path.resolve(__dirname, '../src/client', relative);
        if (cache.has(file)) return cache.get(file);
        let source = readFileSync(file, 'utf8');
        if (file.endsWith('.vue')) {
            source = parse(source).descriptor.scriptSetup.content;
            source += '\nexport { refreshData, savePlayerData, resetPlayerData, playerData, playerDataChanged, errorMessage };';
        }
        const code = ts.transpileModule(source, {
            compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true }
        }).outputText;
        const module = { exports: {} };
        const localRequire = name => {
            if (name.endsWith('/resources/appState')) return { default: state, __esModule: true };
            if (name === 'vue') return { ...require('vue'), onBeforeMount() {} };
            if (name.endsWith('?url')) return require.resolve(name.slice(0, -4));
            if (name.startsWith('.')) {
                const target = path.resolve(path.dirname(file), name);
                return load(existsSync(target + '.ts') ? target + '.ts' : path.join(target, 'index.ts'));
            }
            return require(name);
        };
        new Function('require', 'module', 'exports', code)(localRequire, module, module.exports);
        cache.set(file, module.exports);
        return module.exports;
    }
    return load;
}

async function fixture(t) {
    const SQL = await initSqlJs();
    const db = new SQL.Database();
    // Synthetic rows model only the inspected schemas, never personal save data.
    db.run(`
        CREATE TABLE MiscDataDynamic(DataOwner TEXT, DataName TEXT, DataValue TEXT,
            PRIMARY KEY(DataOwner, DataName));
        INSERT INTO MiscDataDynamic VALUES
            ('Player', 'PlayerFirstName', 'Test'), ('Player', 'PlayerLastName', 'Wizard'),
            ('Player', 'HouseID', 'Ravenclaw'), ('ExperienceManager', 'ExperiencePoints', '1234'),
            ('ExperienceManager', 'LevelUpMult', '1'), ('Player0', 'PerkPoints', '3'),
            ('Player0', 'BaseInventoryCapacity', '20'), ('Other', 'BaseInventoryCapacity', '7');
        CREATE TABLE UpdateAudit(DataOwner TEXT, DataName TEXT);
        CREATE TRIGGER audit AFTER UPDATE ON MiscDataDynamic BEGIN
            INSERT INTO UpdateAudit VALUES(new.DataOwner, new.DataName);
        END;
        CREATE TABLE CollectionDynamic(CategoryID TEXT, SubcategoryID TEXT, ItemID TEXT, ItemState TEXT, UpdateTime INTEGER);
        INSERT INTO CollectionDynamic VALUES
            ('WandStyle','Exploration','h01_m01','Obtained',123),
            ('WandStyle','Exploration','h01_m01','Unknown',0),
            ('WandHandles','Exploration','legacy-handle','Obtained',123),
            ('Exploration','Hogwarts','lore-entry','Obtained',123),
            ('RevelioPages','Hogwarts','legacy-page','Obtained',123),
            ('Traits','Exploration','other','Obtained',123);
        CREATE TABLE LocksDynamic(LockID TEXT PRIMARY KEY, ELockState INTEGER);
        INSERT INTO LocksDynamic VALUES ('h01_m01',0), ('other-lock',1);
        CREATE TABLE LootItemsDynamic(ItemID TEXT, Looted INTEGER, ItemRandomWeight INTEGER, ItemAdjustedWeight INTEGER, Variation TEXT);
        INSERT INTO LootItemsDynamic VALUES ('legacy-handle',1,2,3,NULL), ('legacy-page',1,2,3,NULL), ('other',1,2,3,NULL);
    `);
    const state = { saveGameData: {} };
    const load = loader(state);
    const { SaveGameDB } = load('resources/saveGameDB.ts');
    state.saveGameDB = new SaveGameDB(db.export());
    db.close();
    const manager = load('managers/saveGame.ts').default;
    const inspect = async sql => {
        const copy = new SQL.Database(await state.saveGameDB.getDBBytes());
        try { return copy.exec(sql)[0]?.values || []; }
        finally { copy.close(); }
    };
    const page = load('pages/playerDetailPage.vue');
    return { SQL, state, manager, load, page, inspect };
}

test('Player page applies only the dirty field, preserves progression and other owners, and resets', async t => {
    const h = await fixture(t);
    await h.page.refreshData();
    assert.equal(h.page.playerDataChanged.value, false);
    assert.equal(h.page.playerData.value.BaseInventoryCapacity, '20');
    h.page.playerData.value.FirstName = 'Edited';
    assert.equal(h.page.playerDataChanged.value, true);
    await h.page.savePlayerData();
    assert.equal(h.page.errorMessage.value, '');
    assert.equal(h.page.playerDataChanged.value, false);
    assert.deepEqual(await h.inspect('SELECT * FROM UpdateAudit'), [['Player', 'PlayerFirstName']]);
    assert.deepEqual(await h.inspect("SELECT DataName, DataValue FROM MiscDataDynamic WHERE DataName IN ('ExperiencePoints','PerkPoints') ORDER BY DataName"),
        [['ExperiencePoints', '1234'], ['PerkPoints', '3']]);
    assert.deepEqual(await h.inspect('SELECT * FROM LocksDynamic'), [['h01_m01', 0], ['other-lock', 1]]);
    h.page.playerData.value.LastName = 'Discard this';
    await h.page.resetPlayerData();
    assert.equal(h.page.playerData.value.LastName, 'Wizard');
    assert.equal(h.page.playerDataChanged.value, false);
    await h.manager.modifyPlayerData({ BaseInventoryCapacity: '21' });
    assert.deepEqual(await h.inspect("SELECT DataOwner,DataValue FROM MiscDataDynamic WHERE DataName='BaseInventoryCapacity' ORDER BY DataOwner"),
        [['Other','7'], ['Player0','21']]);
});

test('An unchanged full form and a name changed back produce no UPDATEs', async t => {
    const h = await fixture(t);
    await h.page.refreshData();
    h.page.playerData.value.FirstName = 'Temporary';
    h.page.playerData.value.FirstName = 'Test';
    assert.equal(h.page.playerDataChanged.value, false);
    await h.manager.modifyPlayerData(h.page.playerData.value);
    assert.deepEqual(await h.inspect('SELECT * FROM UpdateAudit'), []);
});

for (const field of ['Exp', 'PerkPoints', 'Level']) {
    test(`Progression ${field} change is refused atomically through manager and page`, async t => {
        const h = await fixture(t);
        const before = await h.state.saveGameDB.getDBBytes();
        await assert.rejects(h.manager.modifyPlayerData({ FirstName: 'Must not persist', [field]: '999' }), /read-only/);
        assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
        await h.page.refreshData();
        h.page.playerData.value[field] = '999';
        await h.page.savePlayerData();
        assert.match(h.page.errorMessage.value, /read-only/);
        assert.equal(h.page.playerDataChanged.value, true);
        assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
    });
}

for (const value of ['', '-1', '1.5', 'NaN', 'Infinity', '1e3', ' 20 ', '2147483648', null, 20]) {
    test(`Invalid capacity ${JSON.stringify(value)} prevents every form mutation`, async t => {
        const h = await fixture(t);
        const before = await h.state.saveGameDB.getDBBytes();
        await assert.rejects(h.manager.modifyPlayerData({ FirstName: 'Must not persist', BaseInventoryCapacity: value }), /whole number|must be text/);
        assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
    });
}

test('Capacity accepts integer storage boundaries', async t => {
    const h = await fixture(t);
    for (const value of ['0', '2147483647']) {
        await h.manager.modifyPlayerData({ BaseInventoryCapacity: value });
        assert.deepEqual(await h.inspect("SELECT DataValue FROM MiscDataDynamic WHERE DataOwner='Player0' AND DataName='BaseInventoryCapacity'"), [[value]]);
    }
});

test('Missing Player rows stay absent and reads retain the existing null-safety', async t => {
    const h = await fixture(t);
    const db = new h.SQL.Database(await h.state.saveGameDB.getDBBytes());
    db.run('DELETE FROM MiscDataDynamic');
    h.state.saveGameDB = new (h.load('resources/saveGameDB.ts').SaveGameDB)(db.export());
    db.close();
    await h.page.refreshData();
    assert.equal(h.page.errorMessage.value, '');
    assert.equal(h.page.playerData.value.FirstName, '');
    assert.equal(h.page.playerData.value.PerkPoints, '0');
    await assert.rejects(h.manager.modifyPlayerData({ FirstName: 'Missing' }), /missing or ambiguous/);
    assert.deepEqual(await h.inspect('SELECT * FROM MiscDataDynamic'), []);
});

test('SQL failure rolls back prior fields in the same Apply', async t => {
    const h = await fixture(t);
    const db = new h.SQL.Database(await h.state.saveGameDB.getDBBytes());
    db.run(`CREATE TRIGGER deny_last BEFORE UPDATE ON MiscDataDynamic WHEN new.DataName='PlayerLastName'
        BEGIN SELECT RAISE(ABORT, 'test constraint'); END;`);
    h.state.saveGameDB = new (h.load('resources/saveGameDB.ts').SaveGameDB)(db.export());
    db.close();
    await assert.rejects(h.manager.modifyPlayerData({ FirstName: 'Changed', LastName: 'Fail' }), /test constraint/);
    assert.deepEqual(await h.inspect('SELECT * FROM UpdateAudit'), []);
    assert.equal((await h.manager.getPlayerData()).FirstName, 'Test');
});

for (const action of ['unlockWandHandles', 'lockWandHandles', 'unlockRevelioPages', 'lockRevelioPages']) {
    test(`${action} fails explicitly without changing any category, loot, or lock`, async t => {
        const h = await fixture(t);
        const before = await h.state.saveGameDB.getDBBytes();
        await assert.rejects(h.manager[action](), /disabled.*not verified/);
        await assert.rejects(h.state.saveGameDB[action](), /disabled.*not verified/);
        assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
        assert.deepEqual(await h.inspect('PRAGMA integrity_check'), [['ok']]);
    });
}

test('UI offers no disabled collection mutations and clearly marks progression read-only', () => {
    const collections = readFileSync(path.join(__dirname, '../src/client/pages/collectionsPage.vue'), 'utf8');
    const player = parse(readFileSync(path.join(__dirname, '../src/client/pages/playerDetailPage.vue'), 'utf8')).descriptor.template.content;
    assert.doesNotMatch(collections, /@click=.*(?:WandHandles|RevelioPages)/);
    assert.match(collections, /Revelio Pages — unavailable/);
    assert.match(collections, /Wand Handles — unavailable/);
    assert.match(player, /v-model="playerData.Exp"\s+readonly/);
    assert.match(player, /v-model="playerData.PerkPoints"\s+readonly/);
});
