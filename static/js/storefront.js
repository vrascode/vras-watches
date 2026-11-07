(() => {
    "use strict";
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const header = document.querySelector("[data-header]");
    const syncHeader = () => header?.classList.toggle("is-scrolled", window.scrollY > 25);
    window.addEventListener("scroll", syncHeader, { passive: true });
    syncHeader();

    const menu = document.querySelector("#mobile-menu");
    const menuToggle = document.querySelector("[data-menu-toggle]");
    menuToggle?.addEventListener("click", () => {
        menu.showModal();
        menuToggle.setAttribute("aria-expanded", "true");
    });
    const closeMenu = () => menu?.close();
    document.querySelector("[data-menu-close]")?.addEventListener("click", closeMenu);
    menu?.querySelectorAll("a").forEach(link => link.addEventListener("click", closeMenu));
    menu?.addEventListener("click", event => { if (event.target === menu && event.offsetX < 0) closeMenu(); });
    menu?.addEventListener("close", () => {
        menuToggle.setAttribute("aria-expanded", "false");
        menuToggle.focus();
    });
    document.querySelectorAll("dialog").forEach(dialog => {
        dialog.addEventListener("keydown", event => {
            if (event.key === "Escape") { event.preventDefault(); dialog.close(); return; }
            if (event.key !== "Tab") return;
            const focusable = [...dialog.querySelectorAll("a[href],button:not(:disabled),input,select,[tabindex='0']")];
            const first = focusable[0];
            const last = focusable.at(-1);
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
        });
    });
    window.matchMedia("(min-width: 901px)").addEventListener("change", event => {
        if (event.matches && menu?.open) closeMenu();
    });

    const notices = document.querySelector("[data-notifications]");
    let noticeTimer;
    const announce = message => {
        if (!notices) return;
        window.clearTimeout(noticeTimer);
        const notice = document.createElement("p");
        notice.className = "notification";
        notice.textContent = message;
        notices.replaceChildren(notice);
        noticeTimer = window.setTimeout(() => notices.replaceChildren(), 7000);
    };
    if (notices?.children.length) noticeTimer = window.setTimeout(() => notices.replaceChildren(), 7000);
    document.querySelectorAll("[data-add-cart]").forEach(form => {
        form.addEventListener("submit", async event => {
            event.preventDefault();
            const button = form.querySelector("button[type=submit]");
            if (button.disabled) return;
            button.disabled = true;
            button.setAttribute("aria-busy", "true");
            try {
                const response = await fetch(form.action, {
                    method: "POST", body: new FormData(form), credentials: "same-origin",
                    headers: { Accept: "application/json" },
                });
                if (!response.headers.get("content-type")?.includes("application/json")) {
                    throw new Error("N\u00e3o foi poss\u00edvel confirmar a altera\u00e7\u00e3o. Atualize a p\u00e1gina e confira o carrinho.");
                }
                const data = await response.json();
                if (!response.ok) throw new Error(data.message);
                document.querySelectorAll("[data-cart-count]").forEach(counter => {
                    counter.textContent = String(data.cart_count);
                });
                announce(data.message);
            } catch (error) {
                announce(error.message || "Conex\u00e3o indispon\u00edvel. Confira o carrinho antes de tentar novamente.");
            } finally {
                button.disabled = false;
                button.removeAttribute("aria-busy");
            }
        });
    });

    if ("IntersectionObserver" in window && !reducedMotion.matches) {
        const reveal = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.remove("reveal-pending");
                    reveal.unobserve(entry.target);
                }
            });
        }, { threshold: .08 });
        document.querySelectorAll("[data-reveal]").forEach(section => {
            section.classList.add("reveal-pending");
            reveal.observe(section);
        });
    }

    const videos = [...document.querySelectorAll("[data-video]")];
    const loadVideo = video => {
        const source = video.querySelector("source[data-src]");
        if (source) {
            source.src = source.dataset.src;
            source.removeAttribute("data-src");
            video.load();
        }
    };
    const pauseOthers = current => videos.forEach(video => { if (video !== current) video.pause(); });
    const playVideo = async video => {
        loadVideo(video);
        try { await video.play(); } catch { /* Autoplay restrictions leave the poster visible. */ }
    };
    videos.forEach(video => {
        const shell = video.closest("[data-video-shell]");
        const toggle = shell.querySelector("[data-video-toggle]");
        const sound = shell.querySelector("[data-video-sound]");
        if (reducedMotion.matches) video.removeAttribute("autoplay");
        const syncToggle = () => {
            shell.classList.toggle("is-playing", !video.paused);
            if (toggle) {
                const label = video.paused ? "Reproduzir v\u00eddeo" : "Pausar v\u00eddeo";
                toggle.textContent = video.paused ? "\u25b6" : "\u23f8";
                toggle.setAttribute("aria-label", label);
                toggle.title = label;
            }
        };
        video.addEventListener("play", () => { pauseOthers(video); syncToggle(); });
        video.addEventListener("pause", syncToggle);
        toggle?.addEventListener("click", () => {
            if (video.paused) { delete video.dataset.userPaused; playVideo(video); }
            else { video.dataset.userPaused = "true"; video.pause(); }
        });
        sound?.addEventListener("click", () => {
            video.muted = !video.muted;
            const label = video.muted ? "Ativar som" : "Silenciar";
            sound.title = label;
            sound.setAttribute("aria-label", label);
            sound.setAttribute("aria-pressed", String(!video.muted));
        });
        video.addEventListener("error", () => {
            shell.classList.add("has-error");
            video.pause();
            video.hidden = true;
            shell.querySelector(".video-fallback").hidden = false;
            shell.querySelector(".video-error").hidden = false;
            shell.querySelector(".video-actions")?.setAttribute("hidden", "");
        });
        const source = video.querySelector("source");
        source?.addEventListener("error", () => video.dispatchEvent(new Event("error")));
        if (video.hasAttribute("data-preview")) {
            const card = video.closest("[data-product-card]");
            card?.addEventListener("pointerenter", event => {
                if (event.pointerType === "mouse" && !reducedMotion.matches && !navigator.connection?.saveData) playVideo(video);
            });
            card?.addEventListener("pointerleave", () => video.pause());
        } else {
            video.addEventListener("pointerdown", () => loadVideo(video), { once: true });
            video.addEventListener("keydown", () => loadVideo(video), { once: true });
        }
    });
    if ("IntersectionObserver" in window) {
        const videoObserver = new IntersectionObserver(entries => {
            entries.forEach(({ target: video, isIntersecting }) => {
                if (!isIntersecting) { video.pause(); return; }
                if (video.hasAttribute("data-preview")) return;
                if (!video.hasAttribute("data-autoplay")) { loadVideo(video); return; }
                if (!reducedMotion.matches && !video.dataset.userPaused && !document.hidden && !navigator.connection?.saveData) playVideo(video);
            });
        }, { threshold: .3 });
        videos.forEach(video => videoObserver.observe(video));
    }
    document.addEventListener("visibilitychange", () => {
        if (document.hidden) videos.forEach(video => video.pause());
    });
    reducedMotion.addEventListener("change", event => {
        if (event.matches) videos.forEach(video => { video.pause(); video.removeAttribute("autoplay"); });
    });

    const zoom = document.querySelector("[data-zoom-dialog]");
    let zoomTrigger;
    document.querySelectorAll("[data-zoom]").forEach(button => {
        button.addEventListener("click", () => {
            zoomTrigger = button;
            const image = zoom.querySelector("[data-zoom-image]");
            image.src = button.dataset.zoom;
            image.alt = button.querySelector("img").alt;
            zoom.showModal();
        });
    });
    document.querySelector("[data-zoom-close]")?.addEventListener("click", () => zoom.close());
    zoom?.addEventListener("close", () => zoomTrigger?.focus());
    document.querySelectorAll("[data-gallery]").forEach(gallery => {
        const track = gallery.querySelector("[data-gallery-track]");
        const counter = gallery.querySelector("[data-gallery-position]");
        const previous = gallery.querySelector("[data-gallery-prev]");
        const next = gallery.querySelector("[data-gallery-next]");
        const move = direction => track.scrollBy({ left: direction * track.clientWidth, behavior: reducedMotion.matches ? "instant" : "smooth" });
        const update = () => {
            const current = Math.round(track.scrollLeft / track.clientWidth);
            if (counter) counter.textContent = `${current + 1} / ${track.children.length}`;
            if (previous) previous.disabled = current === 0;
            if (next) next.disabled = current >= track.children.length - 1;
        };
        previous?.addEventListener("click", () => move(-1));
        next?.addEventListener("click", () => move(1));
        track.addEventListener("scroll", update, { passive: true });
        track.addEventListener("keydown", event => {
            if (event.key === "ArrowRight" || event.key === "ArrowLeft") { event.preventDefault(); move(event.key === "ArrowRight" ? 1 : -1); }
        });
        update();
    });
    document.querySelector("[data-share]")?.addEventListener("click", async event => {
        const button = event.currentTarget;
        const url = document.querySelector("link[rel=canonical]")?.href || window.location.href;
        try {
            if (navigator.share) await navigator.share({ title: button.dataset.shareTitle, url });
            else if (navigator.clipboard) { await navigator.clipboard.writeText(url); announce("Link copiado."); }
            else announce(url);
        } catch (error) { if (error.name !== "AbortError") announce("N\u00e3o foi poss\u00edvel compartilhar. Copie o endere\u00e7o desta p\u00e1gina."); }
    });
})();
