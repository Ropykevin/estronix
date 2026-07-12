/** Product filters — fetch only when Apply is clicked or pagination is used */
(function () {
    var form = document.getElementById("filter-form");
    if (!form) return;

    var resultsContainer = document.querySelector(".col-lg-9");
    var activeController = null;
    var isLoading = false;

    function buildQuery(formEl) {
        var params = new URLSearchParams(new FormData(formEl));
        if (!formEl.querySelector('[name=in_stock]') || !formEl.querySelector('[name=in_stock]').checked) {
            params.delete("in_stock");
        }
        if (!formEl.querySelector('[name=on_sale]') || !formEl.querySelector('[name=on_sale]').checked) {
            params.delete("on_sale");
        }
        return params;
    }

    function setLoading(loading) {
        isLoading = loading;
        var grid = document.getElementById("product-grid-results");
        if (grid) {
            grid.classList.toggle("is-loading", loading);
        }
    }

    function fetchProducts(params) {
        if (activeController) {
            activeController.abort();
        }

        activeController = new AbortController();
        var url = form.dataset.ajaxUrl + "?" + params.toString();
        window.history.replaceState({}, "", url);
        setLoading(true);

        return fetch(url, {
            headers: { "X-Requested-With": "XMLHttpRequest" },
            signal: activeController.signal,
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.html && resultsContainer) {
                    resultsContainer.innerHTML = data.html;
                }
            })
            .catch(function (error) {
                if (error.name !== "AbortError") {
                    window.location.href = url;
                }
            })
            .finally(function () {
                setLoading(false);
                activeController = null;
            });
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        if (isLoading) return;
        fetchProducts(buildQuery(form));
    });

    if (resultsContainer) {
        resultsContainer.addEventListener("click", function (event) {
            var link = event.target.closest(".pagination .page-link");
            if (!link || !link.href || link.getAttribute("aria-disabled") === "true" || link.href === "#") {
                return;
            }

            event.preventDefault();
            if (isLoading) return;

            var url = new URL(link.href, window.location.origin);
            fetchProducts(url.searchParams);
        });
    }
})();
