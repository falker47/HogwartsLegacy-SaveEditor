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
            ('Player', 'HouseID', 'Ravenclaw'), ('ExperienceManager', 'ExperiencePoints', '12025'),
            ('ExperienceManager', 'LevelUpMult', '16'), ('Player0', 'PerkPoints', '3'),
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
            ('Exploration','Hogwarts','LORE_Test_A','Unknown',0),
            ('Exploration','Hogwarts','LORE_Test_B','Obtained',123),
            ('Traits','Exploration','other','Obtained',123);
        CREATE TABLE PerkDynamic(PerkID TEXT PRIMARY KEY);
        INSERT INTO PerkDynamic VALUES ('perk-a');
        CREATE TABLE InventoryDynamic(
            CharacterID TEXT, HolderID TEXT, SlotNumber INTEGER, ItemID TEXT, Count INTEGER
        );
        INSERT INTO InventoryDynamic VALUES
            ('Player0','ResourceInventory',0,'Knuts',1234),
            ('Player0','HealthPotionStorage',0,'WiggenweldPotion',7),
            ('Player0','SanctuaryWheel',1,'MaximaPotion',2),
            ('Other','HealthPotionStorage',0,'WiggenweldPotion',99);
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
    h.page.playerData.value.House = 'Slytherin';
    assert.equal(h.page.playerDataChanged.value, true);
    await h.page.savePlayerData();
    assert.equal(h.page.errorMessage.value, '');
    assert.equal(h.page.playerDataChanged.value, false);
    assert.deepEqual(await h.inspect('SELECT * FROM UpdateAudit'), [['Player', 'HouseID']]);
    assert.deepEqual(await h.inspect("SELECT DataName, DataValue FROM MiscDataDynamic WHERE DataName IN ('ExperiencePoints','PerkPoints') ORDER BY DataName"),
        [['ExperiencePoints', '12025'], ['PerkPoints', '3']]);
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

test('Talent Points are explicitly editable within the vanilla spent + unspent invariant', async t => {
    const h = await fixture(t);
    await h.manager.modifyPlayerData({ PerkPoints: '5' });
    assert.deepEqual(await h.inspect("SELECT DataValue FROM MiscDataDynamic WHERE DataOwner='Player0' AND DataName='PerkPoints'"), [['5']]);
    assert.deepEqual(await h.inspect("SELECT PerkID FROM PerkDynamic"), [['perk-a']]);
    assert.deepEqual(await h.inspect('SELECT * FROM UpdateAudit'), [['Player0', 'PerkPoints']]);
});

test('Talent Points reject totals above the vanilla lifetime maximum atomically', async t => {
    const h = await fixture(t);
    const before = await h.state.saveGameDB.getDBBytes();
    await assert.rejects(
        h.manager.modifyPlayerData({ House: 'Slytherin', PerkPoints: '36' }),
        /cannot exceed 36/
    );
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
});

test('XP level increases are allowed once Talent-system evidence exists', async t => {
    const h = await fixture(t);
    await h.manager.modifyPlayerData({ Exp: '13300' });
    assert.deepEqual(await h.inspect("SELECT DataValue FROM MiscDataDynamic WHERE DataOwner='ExperienceManager' AND DataName='ExperiencePoints'"), [['13300']]);
});

test('Pre-Talent saves can edit XP within a level but cannot skip levels', async t => {
    const h = await fixture(t);
    const db = new h.SQL.Database(await h.state.saveGameDB.getDBBytes());
    db.run("DELETE FROM PerkDynamic");
    db.run("UPDATE MiscDataDynamic SET DataValue='0' WHERE DataOwner='Player0' AND DataName='PerkPoints'");
    h.state.saveGameDB = new (h.load('resources/saveGameDB.ts').SaveGameDB)(db.export());
    db.close();

    await h.manager.modifyPlayerData({ Exp: '12500' });
    assert.deepEqual(await h.inspect("SELECT DataValue FROM MiscDataDynamic WHERE DataOwner='ExperienceManager' AND DataName='ExperiencePoints'"), [['12500']]);

    const beforeJump = await h.state.saveGameDB.getDBBytes();
    await assert.rejects(h.manager.modifyPlayerData({ Exp: '13300' }), /at least one learned talent/);
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), beforeJump);
});

test('XP cannot lower the derived player level and is capped at level 40', async t => {
    const h = await fixture(t);
    const before = await h.state.saveGameDB.getDBBytes();
    await assert.rejects(h.manager.modifyPlayerData({ Exp: '1000' }), /cannot lower the player level/);
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
    await assert.rejects(h.manager.modifyPlayerData({ Exp: '74001' }), /0 to 74000/);
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
});

test('Internal LevelUpMult remains read-only', async t => {
    const h = await fixture(t);
    const before = await h.state.saveGameDB.getDBBytes();
    await assert.rejects(h.manager.modifyPlayerData({ Level: '999' }), /safeguards|progression|editable/i);
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
});

for (const value of ['', '-1', '1.5', 'NaN', 'Infinity', '1e3', ' 20 ', '2147483648', null, 20]) {
    test(`Invalid capacity ${JSON.stringify(value)} prevents every form mutation`, async t => {
        const h = await fixture(t);
        const before = await h.state.saveGameDB.getDBBytes();
        await assert.rejects(h.manager.modifyPlayerData({ House: 'Slytherin', BaseInventoryCapacity: value }), /whole number|must be text/);
        assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
    });
}

test('Galleons are explicit, owner-scoped and independently editable', async t => {
    const h = await fixture(t);
    await h.page.refreshData();
    assert.equal(h.page.playerData.value.Galleons, '1234');
    await h.manager.modifyPlayerData({ Galleons: '4321' });
    assert.deepEqual(
        await h.inspect("SELECT Count FROM InventoryDynamic WHERE CharacterID='Player0' AND HolderID='ResourceInventory' AND ItemID='Knuts'"),
        [[4321]]
    );
});

test('Combat resources include HealthPotionStorage and SanctuaryWheel for Player0 only', async t => {
    const h = await fixture(t);
    const resources = await h.manager.getPlayerCombatResourceInventory();
    assert.deepEqual(
        resources.map(item => [item.HolderID, item.ItemID, item.Count]),
        [['HealthPotionStorage','WiggenweldPotion',7], ['SanctuaryWheel','MaximaPotion',2]]
    );
});

test('Resource inventory scopes HealthPotionStorage to Player0', async t => {
    const h = await fixture(t);
    const resources = await h.manager.getPlayerResourceInventory();
    assert.equal(resources.filter(item => item.ItemID === 'WiggenweldPotion').length, 1);
    assert.equal(resources.find(item => item.ItemID === 'WiggenweldPotion').Count, 7);
});

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
    db.run(`CREATE TRIGGER deny_capacity BEFORE UPDATE ON MiscDataDynamic WHEN new.DataName='BaseInventoryCapacity'
        BEGIN SELECT RAISE(ABORT, 'test constraint'); END;`);
    h.state.saveGameDB = new (h.load('resources/saveGameDB.ts').SaveGameDB)(db.export());
    db.close();
    await assert.rejects(h.manager.modifyPlayerData({ House: 'Slytherin', BaseInventoryCapacity: '21' }), /test constraint/);
    assert.deepEqual(await h.inspect('SELECT * FROM UpdateAudit'), []);
    assert.equal((await h.manager.getPlayerData()).FirstName, 'Test');
});

test('Wand Handles unlock uses WandStyle ownership plus matching usage locks only', async t => {
    const h = await fixture(t);
    const lootBefore = await h.inspect('SELECT * FROM LootItemsDynamic ORDER BY ItemID');
    await h.manager.unlockWandHandles();
    assert.deepEqual(
        await h.inspect("SELECT ItemState FROM CollectionDynamic WHERE CategoryID='WandStyle' ORDER BY rowid"),
        [['Obtained'], ['Obtained']]
    );
    assert.deepEqual(await h.inspect("SELECT ELockState FROM LocksDynamic WHERE LockID='h01_m01'"), [[0]]);
    assert.deepEqual(
        await h.inspect("SELECT ItemState FROM CollectionDynamic WHERE CategoryID='WandHandles'"),
        [['Obtained']]
    );
    assert.deepEqual(await h.inspect('SELECT * FROM LootItemsDynamic ORDER BY ItemID'), lootBefore);
});

test('Wand Handles lock clears WandStyle ownership and matching usage locks only', async t => {
    const h = await fixture(t);
    await h.manager.lockWandHandles();
    assert.deepEqual(
        await h.inspect("SELECT ItemState FROM CollectionDynamic WHERE CategoryID='WandStyle' ORDER BY rowid"),
        [['Unknown'], ['Unknown']]
    );
    assert.deepEqual(await h.inspect("SELECT * FROM LocksDynamic WHERE LockID='h01_m01'"), []);
    assert.deepEqual(await h.inspect("SELECT * FROM LocksDynamic WHERE LockID='other-lock'"), [['other-lock', 1]]);
});

test('Revelio unlock and lock target only LORE_* CollectionDynamic rows', async t => {
    const h = await fixture(t);
    const unrelatedBefore = await h.inspect(
        "SELECT CategoryID,ItemID,ItemState FROM CollectionDynamic WHERE ItemID NOT GLOB 'LORE_*' ORDER BY rowid"
    );

    await h.manager.unlockRevelioPages();
    assert.deepEqual(
        await h.inspect("SELECT ItemID,ItemState FROM CollectionDynamic WHERE ItemID GLOB 'LORE_*' ORDER BY ItemID"),
        [['LORE_Test_A','Obtained'], ['LORE_Test_B','Obtained']]
    );
    assert.deepEqual(
        await h.inspect("SELECT CategoryID,ItemID,ItemState FROM CollectionDynamic WHERE ItemID NOT GLOB 'LORE_*' ORDER BY rowid"),
        unrelatedBefore
    );

    await h.manager.lockRevelioPages();
    assert.deepEqual(
        await h.inspect("SELECT ItemID,ItemState FROM CollectionDynamic WHERE ItemID GLOB 'LORE_*' ORDER BY ItemID"),
        [['LORE_Test_A','Unknown'], ['LORE_Test_B','Unknown']]
    );
});

test('UI exposes restored Wand/Revelio actions and guarded progression editing', () => {
    const collections = readFileSync(path.join(__dirname, '../src/client/pages/collectionsPage.vue'), 'utf8');
    const player = parse(readFileSync(path.join(__dirname, '../src/client/pages/playerDetailPage.vue'), 'utf8')).descriptor.template.content;
    assert.match(collections, /SaveGameManager\.unlockWandHandles/);
    assert.match(collections, /SaveGameManager\.lockWandHandles/);
    assert.match(collections, /SaveGameManager\.unlockRevelioPages/);
    assert.match(collections, /SaveGameManager\.lockRevelioPages/);
    assert.doesNotMatch(collections, /Wand Handles — unavailable|Revelio Pages — unavailable/);
    assert.doesNotMatch(player, /v-model="playerData.Exp"\s+readonly/);
    assert.doesNotMatch(player, /v-model="playerData.PerkPoints"\s+readonly/);
    assert.match(player, /v-model="playerData.Exp"[\s\S]*max="74000"/);
    assert.match(player, /v-model="playerData.PerkPoints"[\s\S]*max="36"/);
});


for (const [field, value] of [
    ['FirstName', 'A'], ['FirstName', 'A substantially longer name'],
    ['FirstName', 'Élodie'], ['LastName', '张𐐀'], ['LastName', ''],
]) {
    test(`Rename guard rejects ${field}=${JSON.stringify(value)} before any mixed Apply mutation`, async t => {
        const h = await fixture(t);
        const before = await h.state.saveGameDB.getDBBytes();
        await assert.rejects(
            h.manager.modifyPlayerData({ Galleons: '4321', House: 'Slytherin', [field]: value }),
            /renam.*unavailable/i
        );
        assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
        assert.deepEqual(await h.inspect('SELECT * FROM UpdateAudit'), []);
    });
}

test('Legacy rename cannot bypass the guard or touch names belonging to other owners', async t => {
    const h = await fixture(t);
    const db = new h.SQL.Database(await h.state.saveGameDB.getDBBytes());
    db.run("INSERT INTO MiscDataDynamic VALUES ('Other', 'PlayerFirstName', 'Other'), ('Other', 'PlayerLastName', 'Person')");
    h.state.saveGameDB = new (h.load('resources/saveGameDB.ts').SaveGameDB)(db.export());
    db.close();
    const before = await h.state.saveGameDB.getDBBytes();
    await assert.rejects(
        h.state.saveGameDB.modifyPlayerName({ FirstName: 'Changed', LastName: 'Name' }),
        /renam.*unavailable/i
    );
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
    await h.state.saveGameDB.modifyPlayerName({ FirstName: 'Test', LastName: 'Wizard' });
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
});

test('Player page reports a rejected programmatic rename without changing the stored name or progression', async t => {
    const h = await fixture(t);
    await h.page.refreshData();
    const before = await h.state.saveGameDB.getDBBytes();
    h.page.playerData.value.FirstName = 'Changed';
    await h.page.savePlayerData();
    assert.match(h.page.errorMessage.value, /renam.*unavailable/i);
    assert.equal(h.page.playerDataChanged.value, true);
    assert.equal((await h.manager.getPlayerData()).FirstName, 'Test');
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
    await h.page.resetPlayerData();
    assert.equal(h.page.playerDataChanged.value, false);
});


// Tagged synthetic GVAS, not evidence of game-specific write semantics.
const int32 = value => { const b = Buffer.alloc(4); b.writeInt32LE(value); return b; };
function fstring(value, wide = false) {
    const bytes = Buffer.from(value + '\0', wide ? 'utf16le' : 'utf8');
    return Buffer.concat([int32(wide ? -bytes.length / 2 : bytes.length), bytes]);
}
function tag(name, kind, payload, extra = Buffer.alloc(0)) {
    return Buffer.concat([fstring(name), fstring(kind), int32(payload.length), int32(0), extra, Buffer.from([0]), payload]);
}
const tags = (...items) => Buffer.concat([...items, fstring('None')]);
const structure = (name, type, value) => tag(name, 'StructProperty', value, Buffer.concat([fstring(type), Buffer.alloc(16)]));
const byteArray = (name, value) => tag(name, 'ArrayProperty', Buffer.concat([int32(value.length), value]), fstring('ByteProperty'));
function metadataTail(name, wide, profile = 2) {
    return Buffer.concat([tags(
        structure('CharacterSaveGameInfo', 'CharacterSaveGameInfo', tags(
            tag('CharacterID', 'IntProperty', int32(profile)),
            tag('CharacterName', 'StrProperty', fstring(name, wide)),
            // Intentionally opaque: do not invent the game's byte-array encoding.
            byteArray('CharacterNameBytes', Buffer.from([255, 0, 128, 1, 2, 3])),
            tag('bIsUsed', 'BoolProperty', Buffer.alloc(0), Buffer.from([1]))
        )),
        structure('DirectoryEntry', 'SaveDirectoryEntry', tags(
            tag('CharacterID', 'IntProperty', int32(profile)),
            tag('FilenameSlot', 'StrProperty', fstring(`HL-0${profile}-00`))
        ))
    ), Buffer.alloc(4)]);
}
function container(db1, db2, tail) {
    return Buffer.concat([
        Buffer.from('GVAS'), int32(2), int32(524), Buffer.alloc(10), fstring('synthetic'),
        int32(3), int32(0), fstring('/Script/PersistentData.PersistentGameData'),
        byteArray('RawDatabaseImage', db1), byteArray('RawExclusiveImage', db2), tail
    ]);
}
const arrayBuffer = bytes => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);

for (const [name, wide] of [['Test Wizard', false], ['Élodie Example', false], ['张𐐀 Example', true]]) {
    test(`DB-only replacement reproduces a stale ${wide ? 'UTF-16' : 'UTF-8'} menu name: ${name}`, async t => {
        const h = await fixture(t);
        const { SaveGameData } = h.load('lib/saveGameData.ts');
        const db1 = await h.state.saveGameDB.getDBBytes();
        const db2 = Buffer.from('untouched secondary database sentinel');
        const tail = metadataTail(name, wide);
        const source = container(db1, db2, tail);
        const save = new SaveGameData(arrayBuffer(source));
        // Model the old DB-only rename (and custom DB import) directly. This
        // characterization must keep passing until coordinated rename is proven.
        const changed = new h.SQL.Database(db1);
        changed.run("UPDATE MiscDataDynamic SET DataValue='A much longer new name' WHERE DataOwner='Player' AND DataName='PlayerFirstName'");
        const generated = save.generateSaveFile(changed.export());
        changed.close();
        const parsed = new SaveGameData(arrayBuffer(generated));
        const check = new h.SQL.Database(parsed.primaryDB);
        assert.deepEqual(check.exec("SELECT DataValue FROM MiscDataDynamic WHERE DataName='PlayerFirstName'")[0].values, [['A much longer new name']]);
        check.close();
        assert.deepEqual(Buffer.from(generated.slice(-tail.length)), tail);
        assert.deepEqual(Buffer.from(parsed.secondaryDB), db2);
        assert.ok(Buffer.from(generated).includes(fstring(name, wide)));
    });
}

for (const tail of [metadataTail('Same Name', true), metadataTail('Same Name', false, 3),
    tags(), Buffer.from('corrupt optional metadata')]) {
    test(`A blocked rename preserves metadata and a subsequent capacity edit preserves the exact tail (${tail.length} bytes)`, async t => {
        const h = await fixture(t);
        const { SaveGameData } = h.load('lib/saveGameData.ts');
        const db2 = Buffer.from('secondary sentinel');
        const original = container(await h.state.saveGameDB.getDBBytes(), db2, tail);
        h.state.saveGameData = new SaveGameData(arrayBuffer(original));
        await assert.rejects(h.manager.modifyPlayerData({ FirstName: 'Changed' }), /renam.*unavailable/i);
        await h.manager.modifyPlayerData({ BaseInventoryCapacity: '21' });
        const generated = await h.manager.generateSaveFile();
        assert.deepEqual(Buffer.from(generated.slice(-tail.length)), tail);
        assert.deepEqual(Buffer.from(new SaveGameData(arrayBuffer(generated)).secondaryDB), db2);
        assert.equal((await h.manager.getPlayerData()).FirstName, 'Test');
        assert.equal((await h.manager.getPlayerData()).BaseInventoryCapacity, '21');
    });
}

test('Rendered Player page keeps both names read-only and capacity editable', async t => {
    const h = await fixture(t);
    await h.page.refreshData();
    const { compileTemplate } = require('@vue/compiler-sfc');
    const { createSSRApp, h: vnode } = require('vue');
    const { renderToString } = require('vue/server-renderer');
    const source = parse(readFileSync(path.join(__dirname, '../src/client/pages/playerDetailPage.vue'), 'utf8')).descriptor.template.content;
    const template = compileTemplate({ source, filename: 'playerDetailPage.vue', id: 'rename-test' });
    assert.deepEqual(template.errors, []);
    const module = { exports: {} };
    const code = ts.transpileModule(template.code, {compilerOptions: { module: ts.ModuleKind.CommonJS }}).outputText;
    new Function('require', 'exports', code)(require, module.exports);
    const app = createSSRApp({ render: module.exports.render, setup: () => ({
        ...h.page, ...h.load('resources/playerEdits.ts')
    }) });
    for (const component of ['v-card', 'v-container', 'v-alert', 'v-row', 'v-col', 'v-btn', 'v-combobox']) {
        app.component(component, { setup: (_, { slots }) => () => vnode('div', slots.default?.()) });
    }
    app.component('v-text-field', {
        props: ['modelValue', 'label', 'readonly'],
        setup: props => () => vnode('input', { value: props.modelValue, readonly: props.readonly === '' || props.readonly === true, 'aria-label': props.label })
    });
    const html = await renderToString(app);
    assert.match(html, /<input[^>]*readonly[^>]*aria-label="First Name"/);
    assert.match(html, /<input[^>]*readonly[^>]*aria-label="Last Name"/);
    assert.match(html, /<input value="20" aria-label="Base Inventory Capacity"/);
    assert.match(html, /Character renaming is unavailable/);
});
