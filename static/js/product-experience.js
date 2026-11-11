(() => {
    "use strict";
    // Preserve normal link navigation, keyboard support and variant-specific cart URLs.
    const stage = document.querySelector(".product-detail");
    document.querySelectorAll("[data-variant-link]").forEach(link => {
        link.addEventListener("click", event => {
            if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button) return;
            if (link.hasAttribute("aria-current")) {
                event.preventDefault();
                return;
            }
            stage?.setAttribute("aria-busy", "true");
        });
    });
    window.addEventListener("pageshow", () => stage?.removeAttribute("aria-busy"));
    document.querySelectorAll(".photo-slide img").forEach(photo => {
        photo.addEventListener("error", () => {
            const button = photo.closest("button");
            if (!button) return;
            photo.hidden = true;
            button.disabled = true;
            button.removeAttribute("data-zoom");
            const fallback = document.createElement("span");
            fallback.className = "media-unavailable";
            fallback.textContent = "Fotografia indisponível. Explore as outras imagens.";
            button.append(fallback);
        }, { once: true });
    });
})();
