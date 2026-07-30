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
        selectedFiles.forEach(function (entry) {
            dataTransfer.items.add(entry.file);
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

        var intro = document.createElement("p");
        intro.className = "small text-muted mb-2";
        intro.textContent = "Selected for upload — remove any wrong image before saving.";
        preview.appendChild(intro);

        var grid = document.createElement("div");
        grid.className = "product-image-gallery";

        selectedFiles.forEach(function (entry, index) {
            var item = document.createElement("div");
            item.className = "product-image-item product-image-pending";

            var img = document.createElement("img");
            img.className = "img-fluid rounded border product-image-preview";
            img.alt = entry.file.name;
            img.src = entry.previewUrl;

            var actions = document.createElement("div");
            actions.className = "product-image-actions";

            var name = document.createElement("span");
            name.className = "small text-truncate";
            name.textContent = entry.file.name;

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

    function addFile(file) {
        if (!file.type.startsWith("image/")) {
            return;
        }

        var reader = new FileReader();
        reader.onload = function (event) {
            selectedFiles.push({
                file: file,
                previewUrl: event.target.result,
            });
            syncInputFiles();
            renderPreview();
        };
        reader.readAsDataURL(file);
    }

    input.addEventListener("change", function () {
        Array.from(input.files || []).forEach(function (file) {
            var key = fileKey(file);
            var exists = selectedFiles.some(function (entry) {
                return fileKey(entry.file) === key;
            });
            if (!exists) {
                addFile(file);
            }
        });
        input.value = "";
    });
})();
