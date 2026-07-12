/** Hero featured product slider */

function initHeroProductSlider() {
    var slider = document.getElementById('heroProductSlider');
    if (!slider) return;

    var slides = slider.querySelectorAll('.hero-slide');
    if (slides.length <= 1) return;

    var dots = slider.querySelectorAll('.hero-slider-dot');
    var prevBtn = slider.querySelector('.hero-slider-prev');
    var nextBtn = slider.querySelector('.hero-slider-next');
    var autoplayMs = parseInt(slider.getAttribute('data-autoplay') || '4500', 10);
    var current = 0;
    var timer = null;
    var isAnimating = false;

    function goTo(index) {
        if (isAnimating || index === current) return;
        isAnimating = true;

        var outgoing = slides[current];
        var incoming = slides[index];

        outgoing.classList.add('is-exiting');
        outgoing.classList.remove('is-active');

        incoming.classList.add('is-active');

        dots.forEach(function (dot, i) {
            dot.classList.toggle('is-active', i === index);
            dot.setAttribute('aria-selected', i === index ? 'true' : 'false');
        });

        current = index;

        window.setTimeout(function () {
            outgoing.classList.remove('is-exiting');
            isAnimating = false;
        }, 560);
    }

    function next() {
        goTo((current + 1) % slides.length);
    }

    function prev() {
        goTo((current - 1 + slides.length) % slides.length);
    }

    function startAutoplay() {
        stopAutoplay();
        timer = window.setInterval(next, autoplayMs);
    }

    function stopAutoplay() {
        if (timer) {
            window.clearInterval(timer);
            timer = null;
        }
    }

    if (nextBtn) nextBtn.addEventListener('click', function () { stopAutoplay(); next(); startAutoplay(); });
    if (prevBtn) prevBtn.addEventListener('click', function () { stopAutoplay(); prev(); startAutoplay(); });

    dots.forEach(function (dot) {
        dot.addEventListener('click', function () {
            var index = parseInt(dot.getAttribute('data-slide'), 10);
            if (!Number.isNaN(index)) {
                stopAutoplay();
                goTo(index);
                startAutoplay();
            }
        });
    });

    slider.addEventListener('mouseenter', stopAutoplay);
    slider.addEventListener('mouseleave', startAutoplay);
    slider.addEventListener('focusin', stopAutoplay);
    slider.addEventListener('focusout', startAutoplay);

    startAutoplay();
}

document.addEventListener('DOMContentLoaded', initHeroProductSlider);
