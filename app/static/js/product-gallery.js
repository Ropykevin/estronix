/** Product detail gallery — zoom, thumbnails, fullscreen, video */
(function () {
    const gallery = document.querySelector('.product-detail-gallery');
    if (!gallery) return;

    const mainImg = gallery.querySelector('.main-product-image');
    const zoomLens = gallery.querySelector('.gallery-zoom-lens');
    const thumbs = gallery.querySelectorAll('.thumbnail-img');
    const fullscreenBtn = document.getElementById('galleryFullscreen');
    const viewer360 = document.getElementById('viewer360');

    thumbs.forEach(function (thumb) {
        thumb.addEventListener('click', function () {
            if (mainImg) mainImg.src = thumb.src;
            thumbs.forEach(function (t) { t.classList.remove('active'); });
            thumb.classList.add('active');
        });
    });

    if (mainImg && zoomLens) {
        mainImg.addEventListener('mousemove', function (e) {
            const rect = mainImg.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            zoomLens.style.backgroundImage = 'url(' + mainImg.src + ')';
            zoomLens.style.backgroundSize = (rect.width * 2) + 'px ' + (rect.height * 2) + 'px';
            zoomLens.style.backgroundPosition = (-x * 2 + 75) + 'px ' + (-y * 2 + 75) + 'px';
            zoomLens.style.display = 'block';
        });
        mainImg.addEventListener('mouseleave', function () {
            zoomLens.style.display = 'none';
        });
    }

    if (fullscreenBtn && mainImg) {
        fullscreenBtn.addEventListener('click', function () {
            const overlay = document.createElement('div');
            overlay.className = 'gallery-fullscreen-overlay';
            overlay.innerHTML = '<img src="' + mainImg.src + '" alt=""><button class="gallery-close">&times;</button>';
            document.body.appendChild(overlay);
            overlay.querySelector('.gallery-close').addEventListener('click', function () {
                overlay.remove();
            });
            overlay.addEventListener('click', function (e) {
                if (e.target === overlay) overlay.remove();
            });
        });
    }

    if (viewer360) {
        viewer360.addEventListener('click', function () {
            alert('360° viewer: integrate with your preferred viewer URL in product.viewer_360_url');
        });
    }
})();
