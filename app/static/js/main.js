/** Estronix Premium UI Interactions */

document.addEventListener('DOMContentLoaded', function () {
    document.documentElement.classList.add('js');
    initNavbarScroll();
    initScrollAnimations();
    initProductGallery();
    initAlertDismiss();
    initDropdownCaretFix();
    initActiveNav();
});

/** Highlight current nav link */
function initActiveNav() {
    var path = window.location.pathname;
    document.querySelectorAll('.site-navbar .nav-link[href]').forEach(function (link) {
        var href = link.getAttribute('href');
        if (!href || href === '#') return;
        if (path === href || (href !== '/' && path.indexOf(href.split('?')[0]) === 0)) {
            link.classList.add('active');
        }
    });
}

/** Navbar glass effect on scroll */
function initNavbarScroll() {
    var navbar = document.getElementById('siteNavbar');
    if (!navbar) return;

    var onScroll = function () {
        if (window.scrollY > 20) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
}

/** Fade-up animations on scroll (Intersection Observer) */
function initScrollAnimations() {
    var elements = document.querySelectorAll('.fade-up');
    if (!elements.length) return;

    function reveal(el) {
        el.classList.add('visible');
    }

    elements.forEach(function (el) {
        var rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            reveal(el);
        } else {
            el.classList.add('will-animate');
        }
    });

    if (!('IntersectionObserver' in window)) {
        elements.forEach(reveal);
        return;
    }

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                reveal(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -20px 0px' });

    elements.forEach(function (el) {
        if (!el.classList.contains('visible')) {
            observer.observe(el);
        }
    });
}

/** Product detail gallery thumbnail switching */
function initProductGallery() {
    var main = document.querySelector('.main-product-image');
    if (!main) return;

    document.querySelectorAll('.thumbnail-img').forEach(function (thumb) {
        thumb.addEventListener('click', function () {
            main.src = this.src;
            document.querySelectorAll('.thumbnail-img').forEach(function (t) {
                t.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
}

/** Auto-dismiss flash alerts */
function initAlertDismiss() {
    document.querySelectorAll('.alert:not(.alert-permanent)').forEach(function (alert) {
        setTimeout(function () {
            if (typeof bootstrap !== 'undefined') {
                var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }
        }, 6000);
    });
}

/** Remove default dropdown caret on icon buttons */
function initDropdownCaretFix() {
    var style = document.createElement('style');
    style.textContent = '.hide-caret::after { display: none !important; }';
    document.head.appendChild(style);
}
