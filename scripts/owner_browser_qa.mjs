// Isolated, fictional owner submission only. Never runs against the real catalog.
import assert from 'node:assert/strict';
import { writeBrowserArtifact } from './qa_artifacts.mjs';

assert.ok(process.env.QA_OWNER_PHOTOS && process.env.QA_OWNER_VARIANT, 'Requires isolated test fixtures');
const base = process.env.QA_BASE_URL;
const debug = process.env.QA_DEBUG_URL || 'http://127.0.0.1:9333';
const target = await (await fetch(`${debug}/json/new?about:blank`, { method: 'PUT' })).json();
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
let sequence = 0;
const pending = new Map();
const browserErrors = [], networkErrors = [];
socket.onmessage = ({ data }) => {
    const message = JSON.parse(data);
    if (message.id) {
        const callback = pending.get(message.id);
        pending.delete(message.id);
        if (message.error) callback?.reject(new Error(message.error.message));
        else callback?.resolve(message.result);
    }
    if (message.method === 'Runtime.exceptionThrown') browserErrors.push(message.params.exceptionDetails);
    if (message.method === 'Runtime.consoleAPICalled' && message.params.type === 'error') browserErrors.push(message.params.args);
    if (message.method === 'Network.responseReceived' && message.params.response.status >= 400) {
        networkErrors.push({ url: message.params.response.url, status: message.params.response.status });
    }
};
const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
    setTimeout(() => { if (pending.delete(id)) reject(new Error(`CDP timeout: ${method}`)); }, 10000).unref();
});
const evaluate = async expression => {
    const result = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
        .catch(error => { throw new Error(`${error.message}: ${expression.slice(0, 180)}`); });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
};
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const waitFor = async expression => {
    for (let attempt = 0; attempt < 150; attempt++) {
        if (await evaluate(expression)) return;
        await sleep(100);
    }
    throw new Error(`Condition timed out: ${expression}`);
};
const go = async path => {
    await send('Page.navigate', { url: base + path });
    await waitFor(`location.href === ${JSON.stringify(base + path)} && document.readyState === 'complete'`);
    await sleep(120);
};
const screenshot = async name => {
    const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    await writeBrowserArtifact('owner', 'screenshots', `owner-${name}.png`, Buffer.from(shot.data, 'base64'));
};

try {
    await send('Page.enable'); await send('DOM.enable'); await send('Runtime.enable'); await send('Network.enable');
    await send('Network.clearBrowserCookies');
    await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    await go('/gestao/entrar/?next=/gestao/catalogo/');
    await evaluate(`document.querySelector('[name=username]').value='qa-owner';
        document.querySelector('[name=password]').value='QA-only-owner-password';
        document.querySelector('form button').click()`);
    await waitFor("location.pathname === '/gestao/catalogo/' && document.querySelector('.manager-grid') !== null");
    assert.equal(await evaluate("document.querySelectorAll('.manager-grid article').length"), 12);
    const widths = [360, 390, 768, 1024, 1440];
    for (const width of widths) {
        await send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: width < 600 });
        for (const [name, path] of [['dashboard', '/gestao/catalogo/'], ['form', '/gestao/catalogo/13/']]) {
            await go(path);
            assert.ok(await evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), `${name} overflow at ${width}`);
            assert.equal(await evaluate("document.querySelectorAll('input[name=preco]').length"), 0);
            await screenshot(`${name}-${width}`);
        }
    }
    assert.equal(await evaluate("document.querySelector('[name=variante]').value"), '');
    assert.equal(await evaluate("document.querySelector('[name=oferta_confirmada]').checked"), false);
    const fields = {
        referencia: 'QA-ONLY-NOT-A-REAL-SKU', fonte: 'https://supplier.example.test/qa-only',
        variante: process.env.QA_OWNER_VARIANT, cor_caixa: 'QA case', cor_mostrador: 'QA dial',
        cor_pulseira: 'QA strap', tipo_pulseira: 'QA type', registro_oferta: 'Isolated QA availability',
        origem: 'Isolated QA color block', comprovante: 'QA fixture only',
    };
    await evaluate(`(() => {
        const fields=${JSON.stringify(fields)};
        for (const [name,value] of Object.entries(fields)) document.querySelector('[name='+name+']').value=value;
        for (const name of ['identidade_confirmada','variante_confirmada','oferta_confirmada','fotos_autorizadas','usar_banner'])
            document.querySelector('[name='+name+']').checked=true;
    })()`);
    const { root } = await send('DOM.getDocument');
    const { nodeId } = await send('DOM.querySelector', { nodeId: root.nodeId, selector: 'input[name=fotos]' });
    await send('DOM.setFileInputFiles', { nodeId, files: JSON.parse(process.env.QA_OWNER_PHOTOS) });
    await waitFor("document.querySelectorAll('[data-upload-preview] img').length === 2");
    await evaluate("document.querySelector('.manager-form button[type=submit]').click()");
    await waitFor("document.querySelector('.notices')?.textContent.includes('publicado e disponível')");
    assert.ok(await evaluate("document.querySelector('.manager-summary').textContent.includes('196,92')"));
    assert.equal(await evaluate("document.querySelectorAll('.current-gallery img').length"), 2);
    for (const width of widths) {
        await send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: width < 600 });
        for (const [name, path] of [['published-home', '/'], ['published-detail', '/produto/13/']]) {
            await go(path);
            await evaluate("Promise.all([...document.images].filter(i => i.getAttribute('src')).map(i => { i.loading='eager'; return i.decode().catch(() => {}); }))");
            assert.ok(await evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), `${name} overflow at ${width}`);
            const broken = await evaluate("[...document.images].filter(i => i.getAttribute('src') && !i.naturalWidth).map(i => ({src:i.src,currentSrc:i.currentSrc,complete:i.complete,loading:i.loading}))");
            assert.equal(broken.length, 0, `${name} broken image: ${JSON.stringify({broken,networkErrors})}`);
            assert.ok(await evaluate("document.body.textContent.includes('196,92')"));
            await screenshot(`${name}-${width}`);
        }
    }
    assert.equal(await evaluate("document.querySelectorAll('[data-gallery-index]').length"), 2);
    await evaluate("document.querySelector('[data-gallery-next]').click()");
    await waitFor("document.querySelector('[data-gallery-position]').textContent === '2 / 2'");
    await evaluate("document.querySelector('[data-add-cart] button').click()");
    await waitFor("document.querySelector('[data-cart-count]').textContent === '1'");
    await go('/carrinho/');
    assert.ok(await evaluate("document.querySelector('.summary-total').textContent.includes('196,92')"));
    await evaluate("document.querySelector('form[action*=adicionar] button').click()");
    await waitFor("document.querySelector('.summary-total')?.textContent.includes('393,84')");
    assert.equal(browserErrors.length, 0, JSON.stringify(browserErrors));
    assert.equal(networkErrors.length, 0, JSON.stringify(networkErrors));
    const report = { fictionalFixturesOnly: true, ownerUploadAndPublication: 'passed', widths, screenshots: 20,
        browserErrors, networkErrors };
    await writeBrowserArtifact('owner', 'reports', 'owner-browser-report.json', JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
} finally {
    await send('Page.close').catch(() => {});
    socket.close();
}
