(function () {
    var input = document.getElementById("productImagesInput");
    var preview = document.getElementById("productImagesPreview");
    if (!input || !preview) {
        return;
    }

    var selectedFiles = [];

    function fileKey(file) {
        return [file.name, file.size, file.lastModified].join(":");
    }

    function syncInputFiles() {
        var dataTransfer = new DataTransfer();
        selectedFiles.forEach(function (file) {
            dataTransfer.items.add(file);
        });
        input.files = dataTransfer.files;
    }

    function renderPreview() {
        preview.innerHTML = "";

        if (!selectedFiles.length) {
            preview.classList.add("d-none");
            return;
        }

        preview.classList.remove("d-none");
        preview.innerHTML =
            '<p class="small text-muted mb-2">Selected for upload — remove any wrong image before saving.</p>';

        var grid = document.createElement("div");
        grid.className = "product-image-gallery";

        selectedFiles.forEach(function (file, index) {
            var item = document.createElement("div");
            item.className = "product-image-item";

            var img = document.createElement("img");
            img.className = "img-fluid rounded border";
            img.alt = file.name;
            img.src = URL.createObjectURL(file);

            var actions = document.createElement("div");
            actions.className = "product-image-actions";

            var name = document.createElement("span");
            name.className = "small text-truncate";
            name.textContent = file.name;

            var removeBtn = document.createElement("button");
            removeBtn.type = "button";
            removeBtn.className = "btn btn-sm btn-outline-danger";
            removeBtn.innerHTML = '<i class="bi bi-trash"></i> Remove';
            removeBtn.addEventListener("click", function () {
                selectedFiles.splice(index, 1);
                syncInputFiles();
                renderPreview();
            });

            actions.appendChild(name);
            actions.appendChild(removeBtn);
            item.appendChild(img);
            item.appendChild(actions);
            grid.appendChild(item);
        });

        preview.appendChild(grid);
    }

    input.addEventListener("change", function () {
        Array.from(input.files || []).forEach(function (file) {
            var key = fileKey(file);
            var exists = selectedFiles.some(function (existing) {
                return fileKey(existing) === key;
            });
            if (!exists) {
                selectedFiles.push(file);
            }
        });
        syncInputFiles();
        renderPreview();
    });
})();
