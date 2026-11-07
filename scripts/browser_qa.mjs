// Dependency-free browser QA via Chrome DevTools Protocol (Node 22+).
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";

const base = process.env.QA_BASE_URL || "http://127.0.0.1:8000";
const debuggerURL = process.env.QA_DEBUG_URL || "http://127.0.0.1:9333";
const target = await (await fetch(`${debuggerURL}/json/new?about:blank`, { method: "PUT" })).json();
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
let sequence = 0;
const pending = new Map();
const browserErrors = [];
const networkErrors = [];
socket.onmessage = ({ data }) => {
    const message = JSON.parse(data);
    if (message.id) {
        const callback = pending.get(message.id);
        pending.delete(message.id);
        if (message.error) callback?.reject(new Error(message.error.message));
        else callback?.resolve(message.result);
    }
    if (message.method === "Runtime.exceptionThrown") browserErrors.push(message.params.exceptionDetails);
    if (message.method === "Runtime.consoleAPICalled" && message.params.type === "error") browserErrors.push(message.params.args);
    if (message.method === "Network.responseReceived" && message.params.response.status >= 400) {
        networkErrors.push({ url: message.params.response.url, status: message.params.response.status });
    }
};
const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
    setTimeout(() => {
        if (pending.has(id)) { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }
    }, 10000).unref();
});
const evaluate = async expression => {
    const result = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
    return result.result.value;
};
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const waitFor = async expression => {
    for (let count = 0; count < 100; count++) {
        if (await evaluate(expression)) return;
        await sleep(100);
    }
    throw new Error(`Condition timed out: ${expression}`);
};
const go = async path => {
    await send("Page.navigate", { url: base + path });
    await waitFor(`location.href === ${JSON.stringify(base + path)} && document.readyState === 'complete'`);
    await evaluate("document.fonts.ready");
    await sleep(120);
};
const key = async value => {
    const virtualKey = { Tab: 9, Escape: 27 }[value];
    await send("Input.dispatchKeyEvent", { type: "rawKeyDown", key: value, code: value, windowsVirtualKeyCode: virtualKey });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: value, code: value, windowsVirtualKeyCode: virtualKey });
};
await mkdir("artifacts", { recursive: true });
try {
    await send("Page.enable");
    await send("Runtime.enable");
    await send("Network.enable");
    await send("Network.clearBrowserCookies");
    if (process.env.QA_CONFIRMED_FIXTURE === "1") {
        // Used only by the isolated Django live-server test, with fictional records.
        const checks = [];
        await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
        for (const width of [360, 1440]) {
            await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 600 });
            await go("/produto/1/");
            assert.equal(await evaluate("document.querySelectorAll('[data-gallery-index]').length"), 2);
            assert.ok(await evaluate("[...document.images].every(i => !i.getAttribute('src') || (i.complete && i.naturalWidth > 0))"));
            assert.equal(await evaluate("document.querySelector('[data-gallery-prev]').disabled"), true);
            await evaluate("document.querySelector('[data-gallery-next]').click()");
            await waitFor("document.querySelector('[data-gallery-position]').textContent === '2 / 2'");
            assert.equal(await evaluate("document.querySelector('[data-gallery-next]').disabled"), true);
            await evaluate("document.querySelector('[data-gallery-index=\"0\"]').click()");
            await waitFor("document.querySelector('[data-gallery-position]').textContent === '1 / 2'");
            await evaluate("document.querySelector('[data-gallery-track]').focus(); document.querySelector('[data-gallery-track]').dispatchEvent(new KeyboardEvent('keydown', { key: 'End', bubbles: true }))");
            await waitFor("document.querySelector('[data-gallery-index=\"1\"]').hasAttribute('aria-current')");
            await evaluate("document.querySelector('[data-gallery-track]').dispatchEvent(new KeyboardEvent('keydown', { key: 'Home', bubbles: true }))");
            await waitFor("document.querySelector('[data-gallery-index=\"0\"]').hasAttribute('aria-current')");
            await evaluate("document.querySelector('[data-zoom]').click()");
            await waitFor("document.querySelector('[data-zoom-dialog]').open");
            assert.ok(await evaluate("document.querySelector('[data-zoom-image]').naturalWidth > 0"));
            await key("Escape");
            await waitFor("!document.querySelector('[data-zoom-dialog]').open");
            await waitFor("document.activeElement.hasAttribute('data-zoom')");
            assert.ok(await evaluate("document.documentElement.scrollWidth <= innerWidth + 1"));
            checks.push({ width, gallery: "arrows, thumbnails, Home/End, zoom, Escape, approved fixture media" });
        }
        // Resize while the second slide is selected must retain selection/alignment.
        await evaluate("document.querySelector('[data-gallery-next]').click()");
        await waitFor("document.querySelector('[data-gallery-position]').textContent === '2 / 2'");
        await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
        await waitFor("Math.abs(document.querySelector('[data-gallery-track]').scrollLeft - document.querySelector('[data-gallery-track]').clientWidth) < 2");
        assert.equal(await evaluate("document.querySelector('.variant-options a[aria-current]').getAttribute('href')"), "/produto/1/");
        await evaluate("document.querySelector('.variant-options a[href=\"/produto/2/\"]').click()");
        await waitFor("location.pathname === '/produto/2/' && document.readyState === 'complete'");
        assert.ok(await evaluate("document.querySelector('.detail-price').textContent.includes('389,00')"));
        assert.equal(await evaluate("document.querySelector('[data-add-cart]').action.endsWith('/adicionar/2/')"), true);
        await evaluate("document.querySelector('[data-add-cart] button').click()");
        await waitFor("document.querySelector('[data-cart-count]').textContent === '1'");
        await go("/carrinho/");
        assert.equal(await evaluate("document.querySelector('.cart-image').getAttribute('href')"), "/produto/2/");
        assert.ok(await evaluate("document.querySelector('.cart-variant').textContent.includes('Preto de teste')"));
        assert.ok(await evaluate("document.querySelector('.summary-total').textContent.includes('389,00')"));
        assert.equal(browserErrors.length, 0, JSON.stringify(browserErrors));
        assert.equal(networkErrors.length, 0, JSON.stringify(networkErrors));
        const report = { fictionalFixturesOnly: true, checks, variantNavigationAndCart: "passed", resize: "passed", browserErrors, networkErrors };
        await writeFile("artifacts/gallery-browser-report.json", JSON.stringify(report, null, 2));
        console.log(JSON.stringify(report, null, 2));
    } else {
    const results = [];
    for (const width of [360, 390, 768, 1024, 1440]) {
        await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 600 });
        for (const [name, path] of [["home", "/"], ["catalog", "/produtos/"], ["detail", "/produto/1/"], ["cart", "/carrinho/"]]) {
            await go(path);
            const layout = await evaluate(`(() => ({
                title: document.title,
                page: document.documentElement.scrollWidth,
                viewport: innerWidth,
                h1: document.querySelector('h1')?.textContent,
                broken: [...document.images].filter(i => i.getAttribute('src') && i.complete && !i.naturalWidth).map(i => i.src),
                overflow: [...document.querySelectorAll('h1,h2,h3,.button,.product-price')].filter(e => e.scrollWidth > e.clientWidth + 2).map(e => e.textContent.trim()),
                placeholders: document.querySelectorAll('a[href="#"]').length
            }))()`);
            assert.ok(layout.page <= width + 1, `Horizontal overflow at ${width}/${name}: ${JSON.stringify(layout)}`);
            assert.equal(layout.broken.length, 0, `Broken images: ${layout.broken}`);
            assert.equal(layout.overflow.length, 0, `Text overflow at ${width}/${name}: ${layout.overflow}`);
            assert.equal(layout.placeholders, 0);
            assert.ok(layout.h1);
            const screenshot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
            await writeFile(`artifacts/${name}-${width}.png`, Buffer.from(screenshot.data, "base64"));
            results.push({ width, page: name, ...layout });
        }
    }
    await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
    await go("/");
    assert.equal(await evaluate("document.querySelectorAll('#lancamentos [data-product-card]').length"), 2);
    await evaluate("document.querySelector('[data-menu-toggle]').click()");
    assert.equal(await evaluate("document.querySelector('#mobile-menu').open"), true);
    for (let count = 0; count < 9; count++) {
        await key("Tab");
        assert.ok(await evaluate("document.activeElement.closest('#mobile-menu') !== null"), "Menu focus escaped modal");
    }
    await key("Escape");
    await waitFor("!document.querySelector('#mobile-menu').open");
    await waitFor("document.activeElement.hasAttribute('data-menu-toggle')");
    await go("/produtos/?q=Genius&ordem=preco_desc");
    assert.equal(await evaluate("document.querySelectorAll('[data-product-card]').length"), 1);
    await evaluate("document.querySelector('[data-add-cart] button').click()");
    await waitFor("document.querySelector('[data-cart-count]').textContent === '1'");
    await go("/carrinho/");
    assert.ok(await evaluate("document.querySelector('.summary-total').textContent.includes('389,00')"));
    await evaluate("document.querySelector('form[action*=adicionar] button').click()");
    await waitFor("document.querySelector('.summary-total')?.textContent.includes('778,00')");
    await evaluate("document.querySelector('form[action*=remover] button').click()");
    await waitFor("document.querySelector('.summary-total')?.textContent.includes('389,00')");
    await evaluate("document.querySelector('form[action*=atualizar] button').click()");
    await waitFor("document.querySelector('.empty-state') !== null");
    await go("/produto/1/");
    await key("Tab");
    assert.equal(await evaluate("document.activeElement.classList.contains('skip-link')"), true);
    await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
    await go("/");
    assert.equal(await evaluate("getComputedStyle(document.documentElement).scrollBehavior"), "auto");
    assert.equal(await evaluate("document.querySelectorAll('.reveal-pending').length"), 0);
    for (let id = 1; id <= 12; id++) {
        await go(`/produto/${id}/`);
        assert.ok(await evaluate("document.querySelector('h1').textContent.startsWith('Vras ' )"));
        assert.equal(await evaluate("document.querySelector('[data-add-cart]').action.endsWith('/adicionar/' + " + id + " + '/')"), true);
        assert.equal(await evaluate("document.querySelectorAll('.variant-options').length"), 0);
    }
    assert.equal(browserErrors.length, 0, JSON.stringify(browserErrors));
    assert.equal(networkErrors.length, 0, JSON.stringify(networkErrors));
    const report = { results, interactions: ["existing launch products", "mobile menu focus trap and Escape", "search and sort", "AJAX add and counter", "cart increment/decrement/remove", "keyboard skip link", "reduced motion", "all 12 product detail pages and cart targets", "no unconfirmed variant selectors"], browserErrors, networkErrors };
    await writeFile("artifacts/browser-report.json", JSON.stringify(report, null, 2));
    console.log(JSON.stringify({ pages: results.length, screenshots: results.length, interactions: report.interactions, browserErrors, networkErrors }, null, 2));
    }
} finally {
    await send("Page.close").catch(() => {});
    socket.close();
}
