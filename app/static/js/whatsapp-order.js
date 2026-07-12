/** Update WhatsApp order link with selected product quantity */
(function () {
    var btn = document.getElementById("whatsappOrderBtn");
    var qtyInput = document.getElementById("productQuantity");
    if (!btn || !qtyInput) return;

    function formatKes(amount) {
        return "KES " + Math.round(amount).toLocaleString("en-KE");
    }

    function buildMessage(qty) {
        var unitPrice = parseFloat(btn.dataset.unitPrice) || 0;
        var lineTotal = unitPrice * qty;
        return (
            "Hi " + btn.dataset.appName + ", I'd like to place an order:\n\n" +
            "*" + btn.dataset.productName + "*\n" +
            "Brand: " + btn.dataset.brand + "\n" +
            "SKU: " + btn.dataset.sku + "\n" +
            "Quantity: " + qty + "\n" +
            "Unit price: " + formatKes(unitPrice) + "\n" +
            "Line total: " + formatKes(lineTotal) + "\n" +
            "Link: " + btn.dataset.productUrl + "\n\n" +
            "Please confirm availability, delivery area, and payment options."
        );
    }

    function updateHref() {
        var qty = Math.max(1, parseInt(qtyInput.value, 10) || 1);
        btn.href = btn.dataset.waBase + "?text=" + encodeURIComponent(buildMessage(qty));
    }

    qtyInput.addEventListener("input", updateHref);
    qtyInput.addEventListener("change", updateHref);
    updateHref();
})();
