/** AJAX cart — add, update, remove without full page reloads */

(function () {
    if (window.__estronixCartInit) return;
    window.__estronixCartInit = true;

    var pendingRequests = new Set();

    function formatKes(amount) {
        return "KES " + Number(amount).toLocaleString("en-KE", { maximumFractionDigits: 0 });
    }

    function updateCartBadges(count) {
        document.querySelectorAll("[data-cart-count]").forEach(function (badge) {
            badge.textContent = count;
            badge.classList.toggle("d-none", count < 1);
        });

        var floatingBtn = document.getElementById("floatingCartBtn");
        if (floatingBtn && count > 0) {
            floatingBtn.classList.remove("is-pulse");
            void floatingBtn.offsetWidth;
            floatingBtn.classList.add("is-pulse");
        }
    }

    function updateCartSubtotals(subtotal) {
        document.querySelectorAll("[data-cart-subtotal], [data-cart-subtotal-total]").forEach(function (el) {
            el.textContent = formatKes(subtotal);
        });
    }

    function showCartToast(message, success) {
        var existing = document.querySelector(".cart-toast");
        if (existing) existing.remove();

        var toast = document.createElement("div");
        toast.className = "cart-toast alert alert-" + (success ? "success" : "danger");
        toast.setAttribute("role", "status");
        toast.innerHTML =
            '<i class="bi bi-' + (success ? "check-circle-fill" : "exclamation-circle-fill") + ' me-2"></i>' +
            message;

        document.body.appendChild(toast);
        requestAnimationFrame(function () {
            toast.classList.add("is-visible");
        });

        setTimeout(function () {
            toast.classList.remove("is-visible");
            setTimeout(function () {
                toast.remove();
            }, 300);
        }, 2800);
    }

    function setButtonLoading(button, loading, loadingText) {
        if (!button) return;
        if (loading) {
            if (!button.dataset.originalHtml) {
                button.dataset.originalHtml = button.innerHTML;
            }
            button.disabled = true;
            button.innerHTML =
                '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>' +
                (loadingText || "Adding…");
        } else if (button.dataset.originalHtml) {
            button.disabled = false;
            button.innerHTML = button.dataset.originalHtml;
        }
    }

    function requestKey(form) {
        return form.action + "|" + new URLSearchParams(new FormData(form)).toString();
    }

    function postForm(form, options) {
        options = options || {};
        var key = requestKey(form);

        if (pendingRequests.has(key)) {
            return Promise.resolve(null);
        }

        pendingRequests.add(key);
        var submitBtn = options.button || form.querySelector('[type="submit"]');
        setButtonLoading(submitBtn, true, options.loadingText);

        return fetch(form.action, {
            method: "POST",
            body: new FormData(form),
            headers: { "X-Requested-With": "XMLHttpRequest" },
            credentials: "same-origin",
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    if (!response.ok) {
                        throw new Error(data.message || "Request failed");
                    }
                    return data;
                });
            })
            .finally(function () {
                pendingRequests.delete(key);
                setButtonLoading(submitBtn, false);
            });
    }

    function replaceCartContent(html) {
        var root = document.getElementById("cartPageRoot");
        if (root) {
            root.innerHTML = html;
        }
    }

    function handleAddToCart(form) {
        return postForm(form, { loadingText: "Adding…" }).then(function (data) {
            if (!data) return;

            if (data.success) {
                updateCartBadges(data.cart_count);
                var name = form.dataset.productName || data.product_name || "Product";
                showCartToast(name + " added to cart", true);
            } else {
                showCartToast(data.message || "Could not add to cart", false);
            }
        });
    }

    function handleCartUpdate(form) {
        return postForm(form, { loadingText: "Updating…" }).then(function (data) {
            if (!data) return;

            if (!data.success) {
                showCartToast(data.message || "Could not update cart", false);
                return;
            }

            updateCartBadges(data.cart_count);
            updateCartSubtotals(data.subtotal);

            if (data.removed) {
                if (data.html) {
                    replaceCartContent(data.html);
                } else {
                    var row = form.closest("[data-cart-row]");
                    if (row) row.remove();
                }
                showCartToast("Item removed from cart", true);
                return;
            }

            var row = form.closest("[data-cart-row]");
            if (row && data.line_total != null) {
                var lineCell = row.querySelector(".cart-line-total");
                if (lineCell) lineCell.textContent = formatKes(data.line_total);
            }

            showCartToast("Cart updated", true);
        });
    }

    function handleCartRemove(form) {
        return postForm(form, { loadingText: "Removing…" }).then(function (data) {
            if (!data) return;

            if (!data.success) {
                showCartToast(data.message || "Could not remove item", false);
                return;
            }

            updateCartBadges(data.cart_count);

            if (data.html) {
                replaceCartContent(data.html);
            } else {
                var row = form.closest("[data-cart-row]");
                if (row) row.remove();
                updateCartSubtotals(data.subtotal);
            }

            showCartToast("Item removed from cart", true);
        });
    }

    document.addEventListener(
        "submit",
        function (event) {
            var form = event.target.closest("form");
            if (!form) return;

            if (form.classList.contains("add-to-cart-form")) {
                event.preventDefault();
                event.stopPropagation();
                handleAddToCart(form).catch(function () {
                    showCartToast("Something went wrong. Please try again.", false);
                });
                return;
            }

            if (form.classList.contains("cart-update-form")) {
                event.preventDefault();
                event.stopPropagation();
                handleCartUpdate(form).catch(function () {
                    showCartToast("Something went wrong. Please try again.", false);
                });
                return;
            }

            if (form.classList.contains("cart-remove-form")) {
                event.preventDefault();
                event.stopPropagation();
                handleCartRemove(form).catch(function () {
                    showCartToast("Something went wrong. Please try again.", false);
                });
            }
        },
        true
    );

    window.EstronixCart = {
        updateCount: updateCartBadges,
    };
})();
