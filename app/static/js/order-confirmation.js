(function () {
    function start(options) {
        var statusUrl = options && options.statusUrl;
        if (!statusUrl) {
            return;
        }

        var attempts = 0;
        var maxAttempts = 40;
        var intervalMs = 3000;

        function poll() {
            attempts += 1;
            fetch(statusUrl, { credentials: "same-origin", headers: { Accept: "application/json" } })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("status");
                    }
                    return response.json();
                })
                .then(function (data) {
                    if (data.paid) {
                        var badge = document.getElementById("orderStatusBadge");
                        if (badge) {
                            badge.textContent = "Paid";
                            badge.style.background = "rgba(34, 197, 94, 0.15)";
                            badge.style.color = "var(--color-success)";
                        }
                        var alert = document.getElementById("mpesaPendingAlert");
                        if (alert) {
                            alert.className = "alert alert-success text-start mb-4";
                            alert.innerHTML =
                                "<strong><i class=\"bi bi-check-circle me-1\"></i> Payment received</strong>" +
                                "<p class=\"mb-0 small mt-2\">Thank you! We are preparing your order.</p>";
                        }
                        return;
                    }
                    if (attempts < maxAttempts) {
                        window.setTimeout(poll, intervalMs);
                    }
                })
                .catch(function () {
                    if (attempts < maxAttempts) {
                        window.setTimeout(poll, intervalMs);
                    }
                });
        }

        window.setTimeout(poll, intervalMs);
    }

    window.EstronixOrderConfirmation = { start: start };
})();
