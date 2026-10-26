const assert = require('node:assert/strict');
const { test } = require('node:test');
const { readFileSync, existsSync } = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
const { parse } = require('@vue/compiler-sfc');
const initSqlJs = require('sql.js');

// Real TS, Vue setup, manager and SQLite; only mounting and app state are supplied.
function loader(state) {
    const cache = new Map();
    return function load(relative) {
        const file = path.resolve(__dirname, '../src/client', relative);
        if (cache.has(file)) return cache.get(file);
        let source = readFileSync(file, 'utf8');
        if (file.endsWith('.vue')) {
            source = parse(source).descriptor.scriptSetup.content;
            source += '\nexport { refreshData, saveData, resourceList, changedResourceList, errorMessage, ready };';
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
    };
}
async function fixture(extraSQL = '', constraints = true) {
    const SQL = await initSqlJs();
    const db = new SQL.Database();
    db.run([
        'CREATE TABLE GearItemsDynamic (',
        'GearID TEXT COLLATE NOCASE NOT NULL, GearVariation TEXT COLLATE NOCASE NOT NULL,',
        'GearLevel INTEGER NOT NULL, OffenseStat INTEGER NOT NULL, DefenseStat INTEGER NOT NULL,',
        'CooldownStat INTEGER, GeneralAbility1 TEXT, GeneralAbility2 TEXT, GeneralAbility3 TEXT,',
        'GearAppearanceOverrideID TEXT, IsIdentified INTEGER, StatUpgrades INTEGER, GearTags TEXT',
        constraints ? ', PRIMARY KEY(GearID,GearVariation));' : ');',
        'INSERT INTO GearItemsDynamic VALUES',
        "('Gloves_A','shared',10,15,20,1,'trait-a','trait-b','trait-c','appearance-a',1,2,'tag-a'),",
        "('Coat_B','shared',11,25,30,2,'coat-a','coat-b','coat-c','appearance-b',1,3,'tag-b'),",
        "('Hat_C','unique',12,35,40,3,'hat-a','hat-b','hat-c','appearance-c',0,0,'tag-c'),",
        "('Npc_D','shared',13,45,50,4,'npc-a','npc-b','npc-c','appearance-d',1,1,'tag-d');",
        'CREATE TABLE InventoryDynamic (',
        'CharacterID TEXT COLLATE NOCASE NOT NULL, HolderID TEXT COLLATE NOCASE NOT NULL,',
        'SlotNumber INTEGER NOT NULL, ItemID TEXT COLLATE NOCASE, Variation TEXT COLLATE NOCASE,',
        'Count INTEGER NOT NULL, PRIMARY KEY(CharacterID,HolderID,SlotNumber));',
        'INSERT INTO InventoryDynamic VALUES',
        "('Player0','ActorBackpack',3,'Gloves_A','shared',1),",
        "('Player0','ActorBackpack',4,'Coat_B','shared',1),",
        "('Player0','CostumeStorage',5,'Hat_C','unique',1),",
        "('Other','ActorBackpack',3,'Npc_D','shared',1);",
        'CREATE TABLE CollectionDynamic(CategoryID TEXT);',
        'CREATE TABLE Unrelated(value TEXT);',
        "INSERT INTO Unrelated VALUES ('sentinel');",
        'CREATE TABLE UpdateAudit(GearID TEXT, Stat TEXT);',
        'CREATE TRIGGER offense_audit AFTER UPDATE OF OffenseStat ON GearItemsDynamic BEGIN',
        "INSERT INTO UpdateAudit VALUES(new.GearID, 'offense'); END;",
        'CREATE TRIGGER defense_audit AFTER UPDATE OF DefenseStat ON GearItemsDynamic BEGIN',
        "INSERT INTO UpdateAudit VALUES(new.GearID, 'defense'); END;",
        extraSQL
    ].join('\n'));
    const state = { saveGameData: {} };
    const load = loader(state);
    state.saveGameDB = new (load('resources/saveGameDB.ts').SaveGameDB)(db.export());
    db.close();
    const manager = load('managers/saveGame.ts').default;
    const inspect = async sql => {
        const copy = new SQL.Database(await state.saveGameDB.getDBBytes());
        try { return copy.exec(sql)[0]?.values || []; }
        finally { copy.close(); }
    };
    return { SQL, state, load, manager, inspect };
}
const glove = stats => ({ GearID: 'Gloves_A', GearVariation: 'shared', SlotNumber: 3, ...stats });
const coat = stats => ({ GearID: 'Coat_B', GearVariation: 'shared', SlotNumber: 4, ...stats });

test('Gear inventory joins the complete item key and returns backpack slot identity', async () => {
    const h = await fixture();
    const rows = await h.manager.getPlayerGearInventory();
    assert.deepEqual(rows.map(r => [r.GearID, r.GearVariation, r.SlotNumber, r.OffenseStat, r.DefenseStat]),
        [['Gloves_A', 'shared', 3, 15, 20], ['Coat_B', 'shared', 4, 25, 30]]);
});
test('A one-stat edit changes only the selected composite-key row and SQL column', async () => {
    const h = await fixture();
    const before = await h.inspect('SELECT * FROM GearItemsDynamic ORDER BY GearID');
    await h.manager.updateGearItem(glove({ OffenseStat: '77' }));
    const after = await h.inspect('SELECT * FROM GearItemsDynamic ORDER BY GearID');
    assert.deepEqual(after, before.map(row => row[0] === 'Gloves_A' ? row.map((v, i) => i === 3 ? 77 : v) : row));
    assert.deepEqual(await h.inspect('SELECT * FROM UpdateAudit'), [['Gloves_A', 'offense']]);
    assert.deepEqual(await h.inspect('SELECT * FROM Unrelated'), [['sentinel']]);
    assert.deepEqual(await h.inspect('PRAGMA integrity_check'), [['ok']]);
});
test('Both zero and signed-32-bit storage maximum serialize as integers', async () => {
    const h = await fixture();
    await h.manager.updateGearItem(glove({ OffenseStat: 0, DefenseStat: '2147483647' }));
    assert.deepEqual(await h.inspect("SELECT OffenseStat,DefenseStat,typeof(OffenseStat),typeof(DefenseStat) FROM GearItemsDynamic WHERE GearID='Gloves_A'"),
        [[0, 2147483647, 'integer', 'integer']]);
    assert.deepEqual(await h.inspect("SELECT OffenseStat,DefenseStat FROM GearItemsDynamic WHERE GearID='Coat_B'"), [[25, 30]]);
});
for (const value of [-1, 1.5, NaN, Infinity, 2147483648, '', ' ', '1.5', '1e2', '-1', '2147483648', '0x10', true, null, undefined]) {
    test('Invalid gear stat is rejected without any mutation: ' + String(value), async () => {
        const h = await fixture();
        const before = await h.state.saveGameDB.getDBBytes();
        await assert.rejects(h.manager.updateGearItem(glove({ OffenseStat: value, DefenseStat: 20 })), /integer|stat/i);
        assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
    });
}
test('A valid first patch and invalid second patch leave the entire batch unchanged', async () => {
    const h = await fixture();
    const before = await h.state.saveGameDB.getDBBytes();
    await assert.rejects(h.manager.updateGearItems([glove({ OffenseStat: 77 }), coat({ DefenseStat: '-1' })]), /integer|stat/i);
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
});
test('A later SQLite trigger failure rolls back all stat and audit changes', async () => {
    const h = await fixture("CREATE TRIGGER reject_coat BEFORE UPDATE ON GearItemsDynamic WHEN NEW.GearID='Coat_B' AND NEW.OffenseStat=999 BEGIN SELECT RAISE(ABORT,'injected gear failure'); END;");
    const before = await h.state.saveGameDB.getDBBytes();
    await assert.rejects(h.manager.updateGearItems([glove({ OffenseStat: 77 }), coat({ OffenseStat: 999 })]), /injected gear failure/);
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
});
for (const [scenario, extraSQL, patch, constraints] of [
    ['shared with another owner', "INSERT INTO InventoryDynamic VALUES('Other','ActorBackpack',8,'Gloves_A','shared',1);", glove({ OffenseStat: 77, DefenseStat: 20 }), true],
    ['missing from inventory', "DELETE FROM InventoryDynamic WHERE ItemID='Gloves_A';", glove({ OffenseStat: 77, DefenseStat: 20 }), true],
    ['stale slot', '', { ...glove({ OffenseStat: 77, DefenseStat: 20 }), SlotNumber: 4 }, true],
    ['equipped item', '', { GearID: 'Hat_C', GearVariation: 'unique', SlotNumber: 5, OffenseStat: 77, DefenseStat: 40 }, true],
    ['ambiguous gear record', "INSERT INTO GearItemsDynamic SELECT * FROM GearItemsDynamic WHERE GearID='Gloves_A';", glove({ OffenseStat: 77, DefenseStat: 20 }), false],
    ['stacked gear reference', "UPDATE InventoryDynamic SET Count=2 WHERE ItemID='Gloves_A';", glove({ OffenseStat: 77, DefenseStat: 20 }), true]
]) {
    test('Unsafe gear target is refused without mutation: ' + scenario, async () => {
        const h = await fixture(extraSQL, constraints);
        const before = await h.state.saveGameDB.getDBBytes();
        await assert.rejects(h.manager.updateGearItem(patch), /missing|ambiguous|shared|changed|backpack|unique|single/i);
        assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
    });
}
test('Readonly and unknown patch fields are rejected instead of being silently ignored', async () => {
    const h = await fixture();
    const before = await h.state.saveGameDB.getDBBytes();
    await assert.rejects(h.manager.updateGearItem(glove({ OffenseStat: 77, DefenseStat: 20, GearLevel: 99 })), /field|stat/i);
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
});
test('Case-insensitive duplicate batch targets are rejected before any UPDATE', async () => {
    const h = await fixture();
    const before = await h.state.saveGameDB.getDBBytes();
    await assert.rejects(h.manager.updateGearItems([
        glove({ OffenseStat: 77 }), { GearID: 'gloves_a', GearVariation: 'SHARED', SlotNumber: 3, DefenseStat: 88 }
    ]), /duplicate|once/i);
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
});
test('No-op gear patches do not issue UPDATE statements', async () => {
    const h = await fixture();
    const before = await h.state.saveGameDB.getDBBytes();
    await h.manager.updateGearItems([]);
    await h.manager.updateGearItem(glove({ OffenseStat: '15', DefenseStat: 20 }));
    assert.deepEqual(await h.inspect('SELECT * FROM UpdateAudit'), []);
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
});
test('Missing active save is an explicit Gear Apply error', async () => {
    const manager = loader({})('managers/saveGame.ts').default;
    await assert.rejects(manager.updateGearItem(glove({ OffenseStat: 77, DefenseStat: 20 })), /load.*save/i);
});


test('Gear page tracks two same-variation items independently and applies both', async () => {
    const h = await fixture();
    const page = h.load('pages/playerInventoryGearPage.vue');
    await page.refreshData();
    assert.equal(page.ready.value, true);
    page.resourceList.value[0].OffenseStat = '77';
    page.resourceList.value[1].DefenseStat = '88';
    assert.equal(page.changedResourceList.value.length, 2);
    await page.saveData();
    assert.equal(page.errorMessage.value, '');
    assert.equal(page.changedResourceList.value.length, 0);
    assert.deepEqual(await h.inspect("SELECT GearID,OffenseStat,DefenseStat FROM GearItemsDynamic WHERE GearID IN ('Gloves_A','Coat_B') ORDER BY GearID"),
        [['Coat_B',25,88], ['Gloves_A',77,20]]);
});
test('Gear page change-back and Reset preserve committed values without SQL writes', async () => {
    const h = await fixture();
    const page = h.load('pages/playerInventoryGearPage.vue');
    await page.refreshData();
    page.resourceList.value[0].OffenseStat = '77';
    page.resourceList.value[0].OffenseStat = '15';
    assert.equal(page.changedResourceList.value.length, 0);
    await page.saveData();
    assert.deepEqual(await h.inspect('SELECT * FROM UpdateAudit'), []);
    page.resourceList.value[0].OffenseStat = '77';
    await page.refreshData();
    assert.equal(page.resourceList.value[0].OffenseStat, 15);
    assert.equal(page.changedResourceList.value.length, 0);
});
test('Gear page preserves every pending edit and shows a batch validation error', async () => {
    const h = await fixture();
    const page = h.load('pages/playerInventoryGearPage.vue');
    await page.refreshData();
    page.resourceList.value[0].OffenseStat = '77';
    page.resourceList.value[1].DefenseStat = '-1';
    const before = await h.state.saveGameDB.getDBBytes();
    await page.saveData();
    assert.match(page.errorMessage.value, /integer|stat/i);
    assert.equal(page.resourceList.value[0].OffenseStat, '77');
    assert.equal(page.resourceList.value[1].DefenseStat, '-1');
    assert.equal(page.changedResourceList.value.length, 2);
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
    await page.refreshData();
    assert.equal(page.errorMessage.value, '');
    assert.equal(page.resourceList.value[1].DefenseStat, 30);
});
test('Gear page displays missing-schema errors instead of rejecting mount or Apply', async () => {
    const h = await fixture('DROP TABLE GearItemsDynamic;');
    const page = h.load('pages/playerInventoryGearPage.vue');
    await page.refreshData();
    assert.equal(page.ready.value, false);
    assert.match(page.errorMessage.value, /GearItemsDynamic/);
    await page.saveData();
    assert.deepEqual(page.resourceList.value, []);
});
test('Gear page preserves inputs and rolls back the batch on SQLite failure', async () => {
    const h = await fixture("CREATE TRIGGER reject_coat BEFORE UPDATE ON GearItemsDynamic WHEN NEW.GearID='Coat_B' BEGIN SELECT RAISE(ABORT,'injected gear failure'); END;");
    const page = h.load('pages/playerInventoryGearPage.vue');
    await page.refreshData();
    page.resourceList.value[0].OffenseStat = '77';
    page.resourceList.value[1].OffenseStat = '88';
    const before = await h.state.saveGameDB.getDBBytes();
    await page.saveData();
    assert.match(page.errorMessage.value, /injected gear failure/);
    assert.equal(page.changedResourceList.value.length, 2);
    assert.deepEqual(await h.state.saveGameDB.getDBBytes(), before);
});
