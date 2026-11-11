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
                if (!video.hasAttribute("data-autoplay")) {
                    if (!navigator.connection?.saveData) loadVideo(video);
                    return;
                }
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
    const zoomButtons = [...document.querySelectorAll("[data-zoom]")];
    const zoomStage = zoom?.querySelector("[data-zoom-stage]");
    const zoomMagnify = zoom?.querySelector("[data-zoom-magnify]");
    const zoomPrevious = zoom?.querySelector("[data-zoom-prev]");
    const zoomNext = zoom?.querySelector("[data-zoom-next]");
    let zoomTrigger;
    let zoomIndex = 0;
    const resetMagnification = () => {
        zoomStage?.classList.remove("is-magnified");
        zoomMagnify?.setAttribute("aria-pressed", "false");
        if (zoomStage) { zoomStage.scrollTop = 0; zoomStage.scrollLeft = 0; }
    };
    const showZoomPhoto = index => {
        zoomIndex = Math.max(0, Math.min(index, zoomButtons.length - 1));
        const button = zoomButtons[zoomIndex];
        if (!button || !zoom) return;
        const original = button.querySelector("img");
        const image = zoom.querySelector("[data-zoom-image]");
        image.src = button.dataset.zoom;
        image.alt = original.alt;
        image.width = original.width;
        image.height = original.height;
        zoom.querySelector("[data-zoom-caption]").textContent = original.alt;
        zoom.querySelector("[data-zoom-position]").textContent = `${zoomIndex + 1} / ${zoomButtons.length}`;
        zoomPrevious.disabled = zoomIndex === 0;
        zoomNext.disabled = zoomIndex === zoomButtons.length - 1;
        resetMagnification();
    };
    zoomButtons.forEach((button, index) => {
        button.addEventListener("click", () => {
            zoomTrigger = button;
            showZoomPhoto(index);
            zoom.showModal();
        });
    });
    zoomPrevious?.addEventListener("click", () => showZoomPhoto(zoomIndex - 1));
    zoomNext?.addEventListener("click", () => showZoomPhoto(zoomIndex + 1));
    const magnify = () => {
        const expanded = zoomStage?.classList.toggle("is-magnified");
        zoomMagnify?.setAttribute("aria-pressed", String(expanded));
    };
    zoomMagnify?.addEventListener("click", magnify);
    zoomStage?.addEventListener("dblclick", magnify);
    zoom?.addEventListener("keydown", event => {
        if (zoomStage?.classList.contains("is-magnified") && event.target === zoomStage) return;
        if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
            event.preventDefault();
            showZoomPhoto(zoomIndex + (event.key === "ArrowRight" ? 1 : -1));
        }
    });
    document.querySelector("[data-zoom-close]")?.addEventListener("click", () => zoom.close());
    zoom?.addEventListener("close", () => { resetMagnification(); zoomTrigger?.focus(); });
    document.querySelectorAll("[data-gallery]").forEach(gallery => {
        const track = gallery.querySelector("[data-gallery-track]");
        const counter = gallery.querySelector("[data-gallery-position]");
        const previous = gallery.querySelector("[data-gallery-prev]");
        const next = gallery.querySelector("[data-gallery-next]");
        const thumbnails = [...gallery.querySelectorAll("[data-gallery-index]")];
        let activeIndex = 0;
        const select = index => track.scrollTo({
            left: Math.max(0, Math.min(index, track.children.length - 1)) * track.clientWidth,
            behavior: reducedMotion.matches ? "instant" : "smooth",
        });
        const move = direction => select(activeIndex + direction);
        const update = () => {
            if (!track.clientWidth) return;
            const current = Math.max(0, Math.min(track.children.length - 1, Math.round(track.scrollLeft / track.clientWidth)));
            if (current !== activeIndex) {
                [...track.children].forEach((slide, index) => {
                    if (index !== current) slide.querySelectorAll("video").forEach(video => video.pause());
                });
            }
            activeIndex = current;
            [...track.children].forEach((slide, index) => { slide.inert = index !== current; });
            if (counter) counter.textContent = `${current + 1} / ${track.children.length}`;
            if (previous) previous.disabled = current === 0;
            if (next) next.disabled = current >= track.children.length - 1;
            thumbnails.forEach((thumbnail, index) => {
                thumbnail.tabIndex = index === current ? 0 : -1;
                if (index === current) thumbnail.setAttribute("aria-current", "true");
                else thumbnail.removeAttribute("aria-current");
            });
        };
        gallery.classList.add("gallery-enhanced");
        thumbnails.forEach((thumbnail, index) => {
            thumbnail.addEventListener("click", () => select(index));
            thumbnail.addEventListener("keydown", event => {
                if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
                event.preventDefault();
                const direction = event.key === "ArrowRight" ? 1 : -1;
                const target = event.key === "Home" ? 0 : event.key === "End" ? thumbnails.length - 1
                    : Math.max(0, Math.min(index + direction, thumbnails.length - 1));
                select(target);
                thumbnails[target].focus({ preventScroll: true });
                thumbnails[target].scrollIntoView({ block: "nearest", inline: "nearest", behavior: "instant" });
            });
        });
        previous?.addEventListener("click", () => move(-1));
        next?.addEventListener("click", () => move(1));
        track.addEventListener("scroll", update, { passive: true });
        track.addEventListener("keydown", event => {
            if (event.target.closest("video, input, select")) return;
            if (event.key === "ArrowRight" || event.key === "ArrowLeft") { event.preventDefault(); move(event.key === "ArrowRight" ? 1 : -1); }
            if (event.key === "Home" || event.key === "End") { event.preventDefault(); select(event.key === "Home" ? 0 : track.children.length - 1); }
        });
        if ("ResizeObserver" in window) new ResizeObserver(() => {
            track.scrollTo({ left: activeIndex * track.clientWidth, behavior: "instant" });
            update();
        }).observe(track);
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
