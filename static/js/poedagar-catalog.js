(() => {
    "use strict";
    const images = [...document.querySelectorAll(".variant-card img")];
    const markUnavailable = image => {
        image.hidden = true;
        const fallback = image.parentElement.querySelector(".photo-fallback");
        if (fallback) fallback.hidden = false;
    };
    images.forEach(image => {
        image.addEventListener("error", () => markUnavailable(image), { once: true });
        if (image.complete && !image.naturalWidth) markUnavailable(image);
    });
    const button = document.querySelector("[data-print-catalog]");
    const status = document.querySelector("[data-print-status]");
    button?.addEventListener("click", async () => {
        button.disabled = true;
        if (status) status.textContent = "Preparando as fotografias para impressão…";
        try {
            await Promise.all(images.map(image => new Promise(resolve => {
                if (image.complete) return resolve();
                const finish = () => {
                    clearTimeout(timer);
                    image.removeEventListener("load", finish);
                    image.removeEventListener("error", finish);
                    resolve();
                };
                const timer = setTimeout(finish, 15000);
                image.addEventListener("load", finish, { once: true });
                image.addEventListener("error", finish, { once: true });
            })));
            const missing = images.filter(image => !image.naturalWidth).length;
            if (status) status.textContent = missing
                ? missing + " fotografia(s) indisponível(is). O catálogo pode ser impresso com as demais."
                : "Catálogo pronto. Escolha Salvar como PDF na janela de impressão.";
            window.print();
        } finally {
            button.disabled = false;
        }
    });
})();
