(function () {
    var modal = document.querySelector("[data-welcome-modal]");

    if (!modal) {
        return;
    }

    var form = modal.querySelector("[data-welcome-form]");
    var emailInput = modal.querySelector("[data-welcome-email]");
    var feedback = modal.querySelector("[data-welcome-feedback]");
    var closeButtons = modal.querySelectorAll("[data-welcome-close]");
    var storageKey = "vrasWelcomeModalDismissedUntil";
    var thirtyDays = 30 * 24 * 60 * 60 * 1000;
    var closeTimer;

    function getDismissedUntil() {
        var value = window.localStorage.getItem(storageKey);
        var timestamp = Number(value);

        return Number.isFinite(timestamp) ? timestamp : 0;
    }

    function rememberDismissal() {
        window.localStorage.setItem(storageKey, String(Date.now() + thirtyDays));
    }

    function shouldOpen() {
        return Date.now() > getDismissedUntil();
    }

    function openModal() {
        modal.classList.remove("is-closing");
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");

        window.setTimeout(function () {
            if (emailInput) {
                emailInput.focus();
            }
        }, 240);
    }

    function closeModal(remember) {
        if (!modal.classList.contains("is-open")) {
            return;
        }

        if (remember) {
            rememberDismissal();
        }

        window.clearTimeout(closeTimer);
        modal.classList.add("is-closing");
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");

        closeTimer = window.setTimeout(function () {
            modal.classList.remove("is-closing");
        }, 280);
    }

    function isValidEmail(value) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    }

    function setFeedback(message, type) {
        feedback.textContent = message;
        feedback.classList.remove("is-error", "is-success");

        if (type) {
            feedback.classList.add("is-" + type);
        }
    }

    closeButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            closeModal(true);
        });
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeModal(true);
        }
    });

    form.addEventListener("submit", function (event) {
        event.preventDefault();

        var email = emailInput.value.trim();

        emailInput.classList.remove("has-error");

        if (!isValidEmail(email)) {
            emailInput.classList.add("has-error");
            setFeedback("Digite um e-mail valido para receber seu beneficio.", "error");
            emailInput.focus();
            return;
        }

        setFeedback("Cadastro recebido. Seu beneficio foi reservado.", "success");
        rememberDismissal();

        window.setTimeout(function () {
            closeModal(false);
        }, 1200);
    });

    window.setTimeout(function () {
        if (shouldOpen()) {
            openModal();
        }
    }, 700);
})();
