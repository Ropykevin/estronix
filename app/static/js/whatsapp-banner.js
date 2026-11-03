(function () {
    var STORAGE_KEY = "estronix_wa_banner_dismissed";
    var DISMISS_DAYS = 7;

    function isDismissed() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) {
                return false;
            }
            var until = parseInt(raw, 10);
            return !isNaN(until) && Date.now() < until;
        } catch (e) {
            return false;
        }
    }

    function dismiss() {
        try {
            var until = Date.now() + DISMISS_DAYS * 24 * 60 * 60 * 1000;
            localStorage.setItem(STORAGE_KEY, String(until));
        } catch (e) {
            /* ignore */
        }
        hideBanner();
    }

    function hideBanner() {
        var banner = document.getElementById("whatsappSlideBanner");
        if (!banner) {
            return;
        }
        banner.classList.remove("is-visible");
        document.body.classList.remove("whatsapp-banner-visible");
        window.setTimeout(function () {
            banner.hidden = true;
        }, 400);
    }

    function showBanner() {
        var banner = document.getElementById("whatsappSlideBanner");
        if (!banner || isDismissed()) {
            return;
        }
        banner.hidden = false;
        window.requestAnimationFrame(function () {
            banner.classList.add("is-visible");
            document.body.classList.add("whatsapp-banner-visible");
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        var closeBtn = document.getElementById("whatsappSlideBannerClose");
        if (closeBtn) {
            closeBtn.addEventListener("click", dismiss);
        }
        if (!document.getElementById("whatsappSlideBanner")) {
            return;
        }
        window.setTimeout(showBanner, 1500);
    });
})();
