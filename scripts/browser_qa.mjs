// Dependency-free browser QA via Chrome DevTools Protocol (Node 22+).
import assert from "node:assert/strict";
import { writeBrowserArtifact } from "./qa_artifacts.mjs";

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
try {
    await send("Page.enable");
    await send("Runtime.enable");
    await send("Network.enable");
    await send("Network.clearBrowserCookies");
    await go("/");
    if (process.env.QA_CONFIRMED_FIXTURE === "1") {
        // Used only by the isolated Django live-server test, with fictional records.
        const checks = [];
        await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
        for (const width of [360, 1440]) {
            await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 600 });
            await go("/");
            assert.ok(await evaluate("document.querySelector('.hero-picture img').complete && document.querySelector('.hero-picture img').naturalWidth > 0"));
            assert.ok(await evaluate(`document.querySelector('.hero-picture img').currentSrc.endsWith('${width === 360 ? 'side' : 'front'}.png')`));
            assert.equal(await evaluate("document.querySelectorAll('.instagram-item').length"), 1);
            assert.ok(await evaluate("document.querySelector('.post-link').href.endsWith('/p/QA-test-only/')"));
            assert.ok(await evaluate("document.querySelector('.campaign img').naturalWidth > 0"));
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
            assert.equal(await evaluate("document.querySelectorAll('.gallery-slide[inert]').length"), 1);
            if (width === 360) {
                await send("Emulation.setTouchEmulationEnabled", { enabled: true });
                const rect = await evaluate("(() => {const r=document.querySelector('[data-gallery-track]').getBoundingClientRect(); return {x:r.left+r.width-30, y:r.top+Math.min(r.height/2,180), width:r.width};})()");
                await send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: rect.x, y: rect.y, id: 1 }] });
                for (let step = 1; step <= 6; step++) {
                    await send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x: rect.x - step * (rect.width - 65) / 6, y: rect.y, id: 1 }] });
                    await sleep(25);
                }
                await send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
                await waitFor("document.querySelector('[data-gallery-position]').textContent === '2 / 2'");
                // Counter changes during the swipe; wait for scroll snapping/inertia to finish.
                await waitFor("Math.abs(document.querySelector('[data-gallery-track]').scrollLeft - document.querySelector('[data-gallery-track]').clientWidth) < 2");
                await sleep(180);
                await send("Emulation.setTouchEmulationEnabled", { enabled: false });
                await evaluate("document.querySelector('[data-gallery-index=\"0\"]').click()");
                await waitFor("document.querySelector('[data-gallery-position]').textContent === '1 / 2'");
                assert.equal(await evaluate("getComputedStyle(document.querySelector('.detail-purchase')).position"), "fixed");
            }
            await evaluate("document.querySelector('[data-zoom]').click()");
            await waitFor("document.querySelector('[data-zoom-dialog]').open");
            assert.ok(await evaluate("document.querySelector('[data-zoom-image]').naturalWidth > 0"));
            await evaluate("document.querySelector('[data-zoom-next]').click()");
            await waitFor("document.querySelector('[data-zoom-position]').textContent === '2 / 2'");
            assert.equal(await evaluate("document.querySelector('[data-zoom-next]').disabled"), true);
            await evaluate("document.querySelector('[data-zoom-magnify]').click()");
            assert.equal(await evaluate("document.querySelector('[data-zoom-magnify]').getAttribute('aria-pressed')"), "true");
            assert.ok(await evaluate("document.querySelector('[data-zoom-stage]').scrollWidth > document.querySelector('[data-zoom-stage]').clientWidth"));
            await evaluate("document.querySelector('[data-zoom-magnify]').click()");
            await evaluate("document.querySelector('[data-zoom-dialog]').dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true }))");
            await waitFor("document.querySelector('[data-zoom-position]').textContent === '1 / 2'");
            await key("Escape");
            await waitFor("!document.querySelector('[data-zoom-dialog]').open");
            await waitFor("document.activeElement.hasAttribute('data-zoom')");
            assert.ok(await evaluate("document.documentElement.scrollWidth <= innerWidth + 1"));
            checks.push({ width, gallery: "arrows, thumbnails, Home/End, touch swipe (mobile), zoom navigation/magnification, inert slides, Escape, approved fixture media" });
        }
        // Resize while the second slide is selected must retain selection/alignment.
        await evaluate("document.querySelector('[data-gallery-next]').click()");
        await waitFor("document.querySelector('[data-gallery-position]').textContent === '2 / 2'");
        await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
        await waitFor("Math.abs(document.querySelector('[data-gallery-track]').scrollLeft - document.querySelector('[data-gallery-track]').clientWidth) < 2");
        assert.equal(await evaluate("document.querySelector('.variant-options a[aria-current]').getAttribute('href')"), "/produto/1/");
        const previousVariantPhoto = await evaluate("document.querySelector('[data-zoom] img').src");
        await evaluate("document.querySelector('.variant-options a[href=\"/produto/2/\"]').click()");
        await waitFor("location.pathname === '/produto/2/' && document.readyState === 'complete'");
        assert.ok(await evaluate("document.querySelector('.detail-price').textContent.includes('389,00')"));
        assert.equal(await evaluate("document.querySelector('[data-add-cart]').action.endsWith('/adicionar/2/')"), true);
        assert.notEqual(await evaluate("document.querySelector('[data-zoom] img').src"), previousVariantPhoto);
        await evaluate("document.querySelector('[data-add-cart] button').click()");
        await waitFor("document.querySelector('[data-cart-count]').textContent === '1'");
        await go("/carrinho/");
        assert.equal(await evaluate("document.querySelector('.cart-image').getAttribute('href')"), "/produto/2/");
        assert.ok(await evaluate("document.querySelector('.cart-variant').textContent.includes('Preto de teste')"));
        assert.ok(await evaluate("document.querySelector('.summary-total').textContent.includes('389,00')"));
        assert.equal(browserErrors.length, 0, JSON.stringify(browserErrors));
        assert.equal(networkErrors.length, 0, JSON.stringify(networkErrors));
        const report = { fictionalFixturesOnly: true, checks, variantNavigationAndCart: "passed", resize: "passed", browserErrors, networkErrors };
        await writeBrowserArtifact("gallery", "reports", "gallery-browser-report.json", JSON.stringify(report, null, 2));
        console.log(JSON.stringify(report, null, 2));
    } else if (await evaluate("document.querySelector('.catalog-preparation') !== null")) {
        // The production catalog intentionally contains only unpublished drafts.
        const results = [];
        for (const width of [360, 390, 768, 1024, 1440]) {
            await send("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 600 });
            for (const [name, path] of [["home", "/"], ["catalog", "/produtos/"], ["cart", "/carrinho/"]]) {
                await go(path);
                assert.ok(await evaluate("document.documentElement.scrollWidth <= innerWidth + 1"));
                assert.equal(await evaluate("document.querySelectorAll('[data-product-card], [data-add-cart]').length"), 0);
                assert.equal(await evaluate("document.body.textContent.includes('R$')"), false);
                assert.equal(await evaluate("document.querySelectorAll('[type=\"application/ld+json\"]').length"), 0);
                const screenshot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
                await writeBrowserArtifact("migration", "screenshots", `migration-${name}-${width}.png`, Buffer.from(screenshot.data, "base64"));
                results.push({ width, page: name, noDraftLeak: true, noOverflow: true });
            }
        }
        await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
        await go("/");
        await evaluate("document.querySelector('[data-menu-toggle]').click()");
        assert.equal(await evaluate("document.querySelector('#mobile-menu').open"), true);
        for (let index = 0; index < 9; index++) {
            await key("Tab");
            assert.ok(await evaluate("document.activeElement.closest('#mobile-menu') !== null"));
        }
        await key("Escape");
        await waitFor("!document.querySelector('#mobile-menu').open");
        await go("/produtos/?q=Army&categoria=Poedagar&ordem=preco_asc");
        assert.equal(await evaluate("document.querySelectorAll('[data-product-card]').length"), 0);
        assert.ok(await evaluate("document.querySelector('.empty-state').textContent.includes('Coleção em preparação')"));
        for (let id = 1; id <= 12; id++) {
            const result = await evaluate(`fetch('/produto/${id}/').then(r => ({status:r.status, redirected:r.redirected, url:r.url}))`);
            assert.equal(result.status, 200);
            assert.equal(result.redirected, true);
            assert.ok(result.url.endsWith("/produtos/"));
        }
        for (let id = 13; id <= 24; id++) {
            assert.equal(await evaluate(`fetch('/produto/${id}/').then(r => r.status)`), 404);
        }
        // Chrome logs an expected failed-resource message for each intentional draft 404.
        const unexpectedNetwork = networkErrors.filter(error => !(error.status === 404 && /\/produto\/(1[3-9]|2[0-4])\/$/.test(error.url)));
        const unexpectedBrowser = browserErrors.filter(error => !Array.isArray(error) || !error.some(arg => (arg.value || "").includes("404")));
        assert.equal(unexpectedNetwork.length, 0, JSON.stringify(unexpectedNetwork));
        assert.equal(unexpectedBrowser.length, 0, JSON.stringify(unexpectedBrowser));
        const report = { mode: "draft-catalog-migration", results, retiredRedirects: 12, protectedDrafts: 12,
                         intentionalDraft404s: networkErrors.filter(error => error.status === 404).length,
                         browserErrors: unexpectedBrowser, networkErrors: unexpectedNetwork };
        await writeBrowserArtifact("migration", "reports", "migration-browser-report.json", JSON.stringify(report, null, 2));
        console.log(JSON.stringify({ mode: report.mode, screenshots: results.length, retiredRedirects: 12,
                                    protectedDrafts: 12, browserErrors: unexpectedBrowser, networkErrors: unexpectedNetwork }, null, 2));
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
            await writeBrowserArtifact("storefront", "screenshots", `${name}-${width}.png`, Buffer.from(screenshot.data, "base64"));
            results.push({ width, page: name, ...layout });
        }
    }
    await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
    await go("/");
    assert.equal(await evaluate("document.querySelectorAll('#lancamentos [data-product-card]').length"), 2);
    assert.equal(await evaluate("document.querySelectorAll('.collection-spotlight').length"), 2);
    assert.ok(await evaluate("document.querySelector('#instagram-title').textContent.includes('NOSSO ESTILO')"));
    assert.equal(await evaluate("document.querySelector('.category-nav')?.textContent.includes('Best Sellers') || false"), false);
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
    await writeBrowserArtifact("storefront", "reports", "browser-report.json", JSON.stringify(report, null, 2));
    console.log(JSON.stringify({ pages: results.length, screenshots: results.length, interactions: report.interactions, browserErrors, networkErrors }, null, 2));
    }
} finally {
    await send("Page.close").catch(() => {});
    socket.close();
}
