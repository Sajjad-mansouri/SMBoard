        (function() {
            const auth = new Auth()
            const navbar = document.getElementById('navbar');
            const hamburger = document.getElementById('hamburger');
            const navLinks = document.getElementById('navLinks');
            const heroIllustration = document.getElementById('heroIllustration');
            const contactForm = document.getElementById('contactForm');
            const lightbox = document.getElementById('lightbox');
            const lightboxClose = document.getElementById('lightboxClose');
            const lightboxImg = document.getElementById('lightboxImg');
            const lightboxTitle = document.getElementById('lightboxTitle');
            const screenshotCards = document.querySelectorAll('.screenshot-card');
            const statNumbers = document.querySelectorAll('.stat-number');
            const revealElements = document.querySelectorAll('.reveal');
            const currentYearSpan = document.getElementById('currentYear');

            // Navbar scroll effect
            window.addEventListener('scroll', () => {
                navbar.classList.toggle('scrolled', window.scrollY > 20);
                if (heroIllustration) heroIllustration.style.transform = `translateY(${window.scrollY * 0.02}px)`;
            });

            // Mobile menu toggle
            hamburger.addEventListener('click', () => {
                const expanded = hamburger.getAttribute('aria-expanded') === 'true';
                hamburger.setAttribute('aria-expanded', !expanded);
                hamburger.classList.toggle('active');
                navLinks.classList.toggle('active');
            });
            navLinks.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navLinks.classList.remove('active');
                hamburger.setAttribute('aria-expanded', 'false');
            }));

            // Counter animation
            const counterObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !entry.target.dataset.animated) {
                        const el = entry.target;
                        const target = parseInt(el.getAttribute('data-count'), 10);
                        let start = 0;
                        const step = Math.ceil(target / (1500 / 16));
                        el.dataset.animated = 'true';
                        const timer = setInterval(() => {
                            start += step;
                            if (start >= target) {
                                el.textContent = target;
                                clearInterval(timer);
                            } else el.textContent = start;
                        }, 16);
                    }
                });
            }, {
                threshold: 0.5
            });
            statNumbers.forEach(num => counterObserver.observe(num));

            // Reveal animations
            const revealObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                        const delay = entry.target.getAttribute('data-delay');
                        if (delay) entry.target.style.transitionDelay = delay + 'ms';
                    }
                });
            }, {
                threshold: 0.15
            });
            revealElements.forEach(el => revealObserver.observe(el));

            // Lightbox functionality (updated to show image and title)
            function openLightbox(card) {
                const img = card.querySelector('.screenshot-img');
                const title = card.querySelector('.screenshot-card-title')?.textContent || 'Screenshot';
                if (img) {
                    lightboxImg.src = img.src;
                    lightboxImg.alt = img.alt;
                }
                lightboxTitle.textContent = title;
                lightbox.classList.add('active');
                lightbox.setAttribute('aria-hidden', 'false');
                document.body.style.overflow = 'hidden';
            }

            function closeLightbox() {
                lightbox.classList.remove('active');
                lightbox.setAttribute('aria-hidden', 'true');
                document.body.style.overflow = '';
                lightboxImg.src = '';
            }

            screenshotCards.forEach(card => {
                card.addEventListener('click', () => openLightbox(card));
            });

            lightboxClose.addEventListener('click', closeLightbox);
            document.getElementById('lightboxOverlay').addEventListener('click', closeLightbox);
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && lightbox.classList.contains('active')) closeLightbox();
            });

            // Contact form validation
            const nameInput = document.getElementById('name');
            const emailInput = document.getElementById('email');
            const messageInput = document.getElementById('message');
            const nameError = document.getElementById('nameError');
            const emailError = document.getElementById('emailError');
            const messageError = document.getElementById('messageError');
            const formFeedback = document.getElementById('formFeedback');

            function validateName() {
                const v = nameInput.value.trim();
                if (v.length < 2) {
                    nameError.textContent = 'Name must be at least 2 characters.';
                    return false;
                }
                nameError.textContent = '';
                return true;
            }

            function validateEmail() {
                const e = emailInput.value.trim();
                if (!e) {
                    emailError.textContent = 'Email is required.';
                    return false;
                }
                if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) {
                    emailError.textContent = 'Please enter a valid email.';
                    return false;
                }
                emailError.textContent = '';
                return true;
            }

            function validateMessage() {
                if (messageInput.value.trim().length < 10) {
                    messageError.textContent = 'Message must be at least 10 characters.';
                    return false;
                }
                messageError.textContent = '';
                return true;
            }
            nameInput.addEventListener('input', validateName);
            emailInput.addEventListener('input', validateEmail);
            messageInput.addEventListener('input', validateMessage);
            contactForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const valid = validateName() & validateEmail() & validateMessage();
                if (!valid) {
                    formFeedback.textContent = 'Please fix the errors above.';
                    formFeedback.style.color = 'var(--color-error)';
                    return;
                }
                formFeedback.textContent = 'Sending...';
                formFeedback.style.color = 'var(--color-text-light)';
                const btn = contactForm.querySelector('button[type="submit"]');

                btn.disabled = true;


                try {
                    const bodyJSON = JSON.stringify({
                        "name": nameInput.value.trim(),
                        "email": emailInput.value.trim(),
                        "message": messageInput.value.trim()
                    })
                    const url = origin + "/api/message/"
                    const response = await fetch(url, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: bodyJSON
                    })
                    const data = await response.json()
                    if (response.ok) {
                        formFeedback.textContent = '✅ Message sent successfully! I\'ll get back to you soon.';
                        formFeedback.style.color = 'var(--color-success)';
                        contactForm.reset();

                    } else {
                        formFeedback.textContent = `${data.detail}`;
                        formFeedback.style.color = 'var(--color-error)';
                    }
                } catch {
                    formFeedback.textContent = '❌ Failed to send. Please try again later.';
                    formFeedback.style.color = 'var(--color-error)';
                } finally {
                    btn.disabled = false;
                }
            });
            if (currentYearSpan) currentYearSpan.textContent = new Date().getFullYear();
        })();