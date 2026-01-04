// ===== LuxuryIQ Landing Page JavaScript =====

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initNavbar();
    initSmoothScroll();
    initScrollAnimations();
    initMobileMenu();
    initTypingEffect();
});

// ===== Navbar Scroll Effect =====
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        // Add scrolled class when page is scrolled
        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        lastScroll = currentScroll;
    });
}

// ===== Smooth Scroll for Anchor Links =====
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));

            if (target) {
                const headerOffset = 80;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });

                // Close mobile menu if open
                const mobileMenu = document.querySelector('.nav-links');
                if (mobileMenu.classList.contains('active')) {
                    mobileMenu.classList.remove('active');
                }
            }
        });
    });
}

// ===== Scroll Animations (Intersection Observer) =====
function initScrollAnimations() {
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');

                // Animate stat numbers if it's a stat section
                if (entry.target.classList.contains('stats-section')) {
                    animateStats();
                }
            }
        });
    }, observerOptions);

    // Observe sections and cards
    const elementsToAnimate = document.querySelectorAll(
        '.section-header, .comparison-card, .database-card, .impact-card, ' +
        '.pricing-card, .step, .feature-item, .stats-section'
    );

    elementsToAnimate.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = `opacity 0.6s ease ${index * 0.05}s, transform 0.6s ease ${index * 0.05}s`;
        observer.observe(el);
    });

    // Add visible styles
    const style = document.createElement('style');
    style.textContent = `
        .visible {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);
}

// ===== Animate Statistics Numbers =====
function animateStats() {
    const stats = document.querySelectorAll('.stat-number[data-count]');

    stats.forEach(stat => {
        if (stat.classList.contains('animated')) return;
        stat.classList.add('animated');

        const target = parseInt(stat.getAttribute('data-count'));
        const duration = 2000;
        const start = performance.now();
        const suffix = stat.textContent.includes('+') ? '+' : '';

        function updateNumber(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function for smooth animation
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const current = Math.floor(easeOutQuart * target);

            stat.textContent = current + suffix;

            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            } else {
                stat.textContent = target + suffix;
            }
        }

        requestAnimationFrame(updateNumber);
    });
}

// ===== Mobile Menu Toggle =====
function initMobileMenu() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');

    if (menuBtn && navLinks) {
        menuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            menuBtn.classList.toggle('active');
        });

        // Add mobile menu styles
        const style = document.createElement('style');
        style.textContent = `
            @media (max-width: 768px) {
                .nav-links {
                    position: fixed;
                    top: 70px;
                    left: 0;
                    right: 0;
                    background: rgba(10, 10, 15, 0.98);
                    backdrop-filter: blur(20px);
                    flex-direction: column;
                    padding: 24px;
                    gap: 16px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                    transform: translateY(-100%);
                    opacity: 0;
                    visibility: hidden;
                    transition: all 0.3s ease;
                }

                .nav-links.active {
                    display: flex;
                    transform: translateY(0);
                    opacity: 1;
                    visibility: visible;
                }

                .nav-links a {
                    padding: 12px 0;
                    font-size: 1rem;
                }

                .nav-links .btn-nav {
                    width: 100%;
                    text-align: center;
                    margin-top: 8px;
                }

                .mobile-menu-btn.active span:nth-child(1) {
                    transform: rotate(45deg) translate(5px, 5px);
                }

                .mobile-menu-btn.active span:nth-child(2) {
                    opacity: 0;
                }

                .mobile-menu-btn.active span:nth-child(3) {
                    transform: rotate(-45deg) translate(5px, -5px);
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// ===== Typing Effect for Chat Demo =====
function initTypingEffect() {
    const assistantMessage = document.querySelector('.chat-message.assistant p');

    if (assistantMessage) {
        const originalText = assistantMessage.innerHTML;

        // Only animate when in viewport
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    typeText(assistantMessage, originalText);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        observer.observe(assistantMessage);
    }
}

function typeText(element, html) {
    element.innerHTML = '';
    element.style.opacity = '1';

    // Parse HTML and type character by character
    let charIndex = 0;
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    const textContent = tempDiv.textContent || tempDiv.innerText;

    function type() {
        if (charIndex < textContent.length) {
            // For simplicity, just show the text progressively
            const progress = charIndex / textContent.length;
            const htmlProgress = Math.floor(progress * html.length);

            // Find a good breaking point (not in the middle of a tag)
            let breakPoint = htmlProgress;
            while (breakPoint < html.length && html[breakPoint] !== ' ' && html[breakPoint] !== '<') {
                breakPoint++;
            }

            element.innerHTML = html.substring(0, breakPoint);
            charIndex += 2; // Speed up by incrementing by 2

            setTimeout(type, 15);
        } else {
            element.innerHTML = html;
        }
    }

    // Small delay before starting
    setTimeout(type, 500);
}

// ===== Parallax Effect for Hero Background =====
window.addEventListener('scroll', () => {
    const hero = document.querySelector('.hero-bg');
    if (hero) {
        const scrolled = window.pageYOffset;
        hero.style.transform = `translateY(${scrolled * 0.3}px)`;
    }
});

// ===== Add hover effects for cards =====
document.querySelectorAll('.database-card, .pricing-card, .impact-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-8px)';
    });

    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
    });
});

// ===== Prevent default on placeholder links =====
document.querySelectorAll('a[href="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
        if (link.getAttribute('href') === '#' && !link.closest('.nav-links')) {
            e.preventDefault();
        }
    });
});
