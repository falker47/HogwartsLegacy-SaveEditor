const assert = require('node:assert/strict');
const { test } = require('node:test');
const { readFileSync, mkdtempSync, rmSync, existsSync } = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const vm = require('node:vm');
const ts = require('typescript');
const { parse } = require('@vue/compiler-sfc');

const repo = path.resolve(__dirname, '../..');

function python(root, request) {
    const child = spawnSync(process.env.PYTHON || 'python', [path.join(repo, 'tests/editor_harness.py')], {
        input: JSON.stringify({ root, ...request }), encoding: 'utf8', maxBuffer: 4 * 1024 * 1024
    });
    assert.equal(child.status, 0, child.stderr);
    return JSON.parse(child.stdout);
}

// Execute unmodified TS modules and Vue script-setup bodies. Only the router
// and browser/desktop boundaries are simulated; extraction, SQL and helpers run.
function moduleLoader(context) {
    const cache = new Map();
    function load(filename) {
        if (cache.has(filename)) return cache.get(filename).exports;
        let source = readFileSync(filename, 'utf8');
        if (filename.endsWith('.vue')) {
            source = parse(source).descriptor.scriptSetup.content;
            source += '\nexport { downloadSave };';
            if (filename.endsWith('saveFilePage.vue')) {
                source += '\nexport { downloadDB, downloadCustomSave, handleDB1FileUpload, handleDB2FileUpload };';
            } else {
                source += '\nexport { handleFileUpload };';
            }
        }
        const compiled = ts.transpileModule(source, {
            compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true }
        }).outputText;
        const module = { exports: {} };
        cache.set(filename, module);
        const localRequire = (name) => {
            if (name === 'vue-router') return { useRouter: () => ({ push: async () => {} }) };
            if (name.endsWith('?url')) return require.resolve(name.slice(0, -4));
            if (name.startsWith('.')) {
                const resolved = path.resolve(path.dirname(filename), name);
                return load(existsSync(resolved + '.ts') ? resolved + '.ts' : path.join(resolved, 'index.ts'));
            }
            return require(name);
        };
        vm.runInContext(`(function(require, module, exports) {${compiled}\n})`, context, { filename })(
            localRequire, module, module.exports
        );
        return module.exports;
    }
    return (relative) => load(path.join(repo, 'HLSE-src/src/client', relative));
}

async function harness(t, variant) {
    const root = mkdtempSync(path.join(tmpdir(), 'hlse-raw-'));
    t.after(() => rmSync(root, { recursive: true, force: true }));
    const fixture = python(root, { op: 'fixture' });
    const timers = [];
    const pending = [];
    const elements = [];
    const urls = new Map();
    const calls = [];
    let listener;
    const state = { readError: null, fetchError: false, apiError: false, badBase64: false, destination: undefined, returncode: 0 };
    const input = { dispatchEvent(event) { assert.equal(event.type, 'change'); } };
    const document = {
        body: { appendChild(element) { element.attached = true; } },
        querySelector: () => input,
        addEventListener(type, fn, capture) {
            assert.equal(type, 'click'); assert.equal(capture, true); listener = fn;
        },
        createElement(tag) {
            const element = {
                tag, style: {}, attached: false, innerHTML: '',
                remove() { this.attached = false; },
                closest(name) { return name === tag ? this : null; },
                hasAttribute(name) { return Object.hasOwn(this, name); },
                getAttribute(name) { return this[name] ?? null; },
                click() {
                    assert.equal(this.attached, true, 'actual helper attaches its programmatic anchor');
                    const event = {
                        target: this, prevented: false, stopped: false,
                        preventDefault() { this.prevented = true; },
                        stopPropagation() { this.stopped = true; }
                    };
                    pending.push(Promise.resolve(listener(event)));
                    assert.equal(event.prevented, true);
                    assert.equal(event.stopped, true);
                }
            };
            elements.push(element);
            return element;
        }
    };
    class FileReader {
        readAsDataURL(blob) {
            pending.push((async () => {
                if (state.readError) {
                    this.error = new Error('synthetic blob read error');
                    await this[state.readError]?.();
                } else {
                    const b64 = state.badBase64 ? '%%%' : Buffer.from(await blob.arrayBuffer()).toString('base64');
                    this.result = `data:${blob.type};base64,${b64}`;
                    await this.onload();
                }
            })());
        }
    }
    async function api(method, args) {
        if (state.apiError) throw new Error('synthetic API rejection');
        const destination = state.destination === undefined ? path.join(root, args[1] || 'unused.sqlite') : state.destination;
        const response = python(root, { op: 'api', method, args, destination, returncode: state.returncode });
        calls.push({ method, args, ...response });
        return response.result;
    }
    const context = vm.createContext({
        console: { ...console, log() {} }, Blob, Uint8Array, ArrayBuffer, DataView, atob, document, FileReader,
        File: class extends Blob { constructor(parts, name, opts) { super(parts, opts); this.name = name; } },
        DataTransfer: class { files = []; items = { add: (file) => this.files.push(file) }; },
        Event: class { constructor(type) { this.type = type; } },
        URL: { createObjectURL(blob) { const url = `blob:test-${urls.size}`; urls.set(url, blob); return url; },
            revokeObjectURL(url) { urls.delete(url); } },
        fetch: async (url) => {
            if (state.fetchError) throw new Error('synthetic fetch error');
            assert.ok(urls.has(url)); return { blob: async () => urls.get(url) };
        },
        setTimeout(fn, delay) { timers.push({ fn, delay }); },
        pywebview: { api: {
            get_file_data: async () => fixture.save,
            get_file_name: async () => 'loaded.dat',
            save_edited_file: (...args) => api('save_edited_file', args),
            export_database: (...args) => api('export_database', args),
            close_window: (...args) => api('close_window', args)
        } }
    });
    async function settle() {
        while (pending.length) await Promise.all(pending.splice(0));
    }
    async function flushTimers() {
        for (const { fn } of timers.splice(0)) await fn();
        await settle();
    }
    vm.runInContext(fixture.bridges[variant], context);
    await flushTimers();
    assert.ok(listener);
    assert.equal(input.files[0].name, 'loaded.dat');
    assert.deepEqual(Buffer.from(await input.files[0].arrayBuffer()), Buffer.from(fixture.save, 'base64'));
    const load = moduleLoader(context);
    const app = load('managers/application.ts').default;
    const handler = load('components/fileHandler.vue');
    // Complete the input change through the real upload handler and app manager.
    await handler.handleFileUpload({ srcElement: input });
    assert.equal(app.appState.isSaveFileLoaded, true);
    const page = load('pages/saveFilePage.vue');
    const manager = load('managers/saveGame.ts').default;
    const appState = load('resources/appState.ts').default;
    await appState.saveGameDB.getDBBytes(); // finish real sql.js initialization
    return { root, fixture, calls, elements, state, page, handler, manager, appState, load,
        settle, flushTimers, context, inspect: () => python(root, { op: 'inspect' }),
        activeOverlays: () => elements.filter(e => e.tag === 'div' && e.attached) };
}

for (const variant of ['external', 'fallback']) {
    test(`${variant}: DB1/DB2 programmatic downloads export raw bytes without write-back`, async (t) => {
        const h = await harness(t, variant);
        // Pending SQL changes must not silently alter the meaning of raw export.
        await h.appState.saveGameDB.modifyPlayerPerkPoints('99');
        assert.notDeepEqual(Buffer.from(await h.appState.saveGameDB.getDBBytes()), Buffer.from(h.fixture.payloads[0], 'base64'));
        for (const secondary of [false, true]) {
            await h.page.downloadDB(secondary);
            await h.settle();
        }
        const misrouted = h.calls.filter(c => c.method === 'save_edited_file');
        if (misrouted.length) {
            for (const [index, call] of misrouted.entries()) {
                assert.equal(call.args[0], h.fixture.payloads[index]);
                assert.deepEqual(call.subprocess, [[
                    'mock-hlsaves', '-c', path.join(h.root, 'loaded.edited'), path.join(h.root, 'original.sav')
                ]]);
            }
            assert.deepEqual(readFileSync(path.join(h.root, 'loaded.edited')), Buffer.from(h.fixture.payloads[1], 'base64'));
            t.diagnostic('Baseline evidence: both SQLite payloads reached real save_edited_file, wrote loaded.edited, and invoked mocked hlsaves -c against original.sav.');
        }
        assert.equal(h.calls.filter(c => c.method === 'save_edited_file').length, 0,
            'raw SQLite must never be sent to save_edited_file / hlsaves');
        assert.deepEqual(h.calls.map(c => c.method), ['export_database', 'export_database']);
        for (const [index, call] of h.calls.entries()) {
            const name = `sqldb${index + 1}.sqlite`;
            assert.deepEqual(call.args, [h.fixture.payloads[index], name]);
            assert.deepEqual(call.result, { success: true });
            assert.deepEqual(call.subprocess, []);
            assert.deepEqual(call.status, []);
            assert.equal(call.closed, 0);
            assert.equal(call.dialogs[0].kwargs.save_filename, name);
        }
        await h.flushTimers();
        assert.equal(h.activeOverlays().length, 0);
        assert.ok(h.elements.every(e => !e.innerHTML.includes('Save Updated')));
        const files = h.inspect();
        for (const [name, info] of Object.entries(h.fixture.files)) assert.deepEqual(files[name], info);
        for (const index of [1, 2]) {
            assert.deepEqual(files[`sqldb${index}.sqlite`], files[`fixture${index}.sqlite`]);
            assert.equal(files[`sqldb${index}.sqlite`].integrity, 'ok');
            assert.equal(files[`sqldb${index}.sqlite`].identity, `database-${index}`);
            assert.deepEqual(readFileSync(path.join(h.root, `sqldb${index}.sqlite`)), Buffer.from(h.fixture.payloads[index - 1], 'base64'));
        }
        assert.ok(!Object.keys(files).some(name => name.endsWith('.edited')));
        assert.equal(h.calls.filter(c => c.method === 'close_window').length, 0);
    });

    for (const producer of ['fileHandler', 'savePage', 'custom']) {
        for (const returncode of [0, 1]) {
            test(`${variant}: ${producer} retains write-back, status and close behavior (exit ${returncode})`, async (t) => {
                const h = await harness(t, variant);
                h.state.returncode = returncode;
                let expected;
                if (producer === 'custom') {
                    // Distinct uploaded databases, intentionally swapped, exercise both upload handlers.
                    const db1 = Buffer.from(h.fixture.payloads[1], 'base64');
                    const db2 = Buffer.from(h.fixture.payloads[0], 'base64');
                    await h.page.handleDB1FileUpload({ srcElement: { files: [new Blob([db1])] } });
                    await h.page.handleDB2FileUpload({ srcElement: { files: [new Blob([db2])] } });
                    expected = await h.manager.generateSaveFile(db1, db2);
                    await h.page.downloadCustomSave();
                } else {
                    await h.appState.saveGameDB.modifyPlayerPerkPoints('99');
                    expected = await h.manager.generateSaveFile();
                    await (producer === 'fileHandler' ? h.handler : h.page).downloadSave();
                }
                await h.settle();
                assert.equal(h.calls.length, 1);
                const call = h.calls[0];
                assert.equal(call.method, 'save_edited_file');
                assert.equal(call.args[0], Buffer.from(expected).toString('base64'));
                assert.deepEqual(readFileSync(path.join(h.root, 'loaded.edited')), Buffer.from(expected));
                assert.deepEqual(call.subprocess, [[
                    'mock-hlsaves', '-c', path.join(h.root, 'loaded.edited'), path.join(h.root, 'original.sav')
                ]]);
                assert.deepEqual(call.dialogs, []);
                assert.equal(call.result.success, returncode === 0);
                assert.equal(call.status[0][0], returncode ? 'error' : 'success');
                const anchor = h.elements.find(e => e.tag === 'a');
                assert.equal(anchor.download, producer === 'custom' ? 'hlcustomsave.sav' : 'hlsave.sav');
                await h.flushTimers();
                assert.equal(h.calls.filter(c => c.method === 'close_window').length, returncode ? 0 : 1);
                if (!returncode) assert.equal(h.calls[1].closed, 1);
                else assert.equal(h.activeOverlays().length, 0);
            });
        }
    }

    for (const failure of ['cancel', 'write', 'fetch', 'onerror', 'onabort', 'api', 'base64']) {
        test(`${variant}: ${failure} clears the overlay and allows another export`, async (t) => {
            const h = await harness(t, variant);
            if (failure === 'cancel') h.state.destination = null;
            if (failure === 'write') h.state.destination = path.join(h.root, 'missing-parent', 'db.sqlite');
            if (failure === 'fetch') h.state.fetchError = true;
            if (failure === 'onerror' || failure === 'onabort') h.state.readError = failure;
            if (failure === 'api') h.state.apiError = true;
            if (failure === 'base64') h.state.badBase64 = true;
            await h.page.downloadDB(false);
            await h.settle();
            if (failure === 'cancel') assert.deepEqual(h.calls[0].result, { success: false, cancelled: true });
            if (failure === 'write' || failure === 'base64') assert.equal(h.calls[0].result.success, false);
            await h.flushTimers();
            assert.equal(h.activeOverlays().length, 0);
            assert.deepEqual(h.inspect(), h.fixture.files);
            assert.ok(h.calls.every(c => c.method === 'export_database' && !c.subprocess.length && !c.status.length));
            assert.ok(h.elements.every(e => !e.innerHTML.includes('Save Updated')));
            Object.assign(h.state, { destination: undefined, fetchError: false, readError: null, apiError: false, badBase64: false });
            await h.page.downloadDB(true);
            await h.settle();
            await h.flushTimers();
            assert.equal(h.calls.at(-1).result.success, true);
            assert.equal(h.activeOverlays().length, 0);
            assert.deepEqual(readFileSync(path.join(h.root, 'sqldb2.sqlite')), Buffer.from(h.fixture.payloads[1], 'base64'));
        });
    }

    test(`${variant}: unknown download names and non-blob links never recompress`, async (t) => {
        const h = await harness(t, variant);
        const { downloadBlob } = h.load('lib/blobUtils.ts');
        for (const name of ['unknown.sav', 'unknown.sqlite', 'SQLDB1.SQLITE', '', '../sqldb1.sqlite']) {
            downloadBlob(Buffer.from(h.fixture.payloads[0], 'base64'), name);
            await h.settle();
            await h.flushTimers();
        }
        const anchor = h.context.document.createElement('a');
        anchor.download = 'sqldb1.sqlite';
        anchor.href = 'https://example.invalid/database';
        h.context.document.body.appendChild(anchor);
        anchor.click();
        await h.settle();
        await h.flushTimers();
        assert.deepEqual(h.calls, []);
        assert.equal(h.activeOverlays().length, 0);
        assert.deepEqual(h.inspect(), h.fixture.files);
    });
}
