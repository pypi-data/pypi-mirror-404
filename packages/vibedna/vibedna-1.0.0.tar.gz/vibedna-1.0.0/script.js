/**
 * VibeDNA Landing Page JavaScript
 * Interactive features and animations
 *
 * © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
    initDNABackground();
    initNavigation();
    initDemoEncoder();
    initCodeTabs();
    initCopyButtons();
    initScrollAnimations();
    initHelixAnimation();
});

/**
 * DNA Background Animation using Canvas
 */
function initDNABackground() {
    const canvas = document.getElementById('dnaCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationId;
    let particles = [];

    // Nucleotide colors
    const colors = {
        A: '#00D4FF', // Cyan - Adenine
        T: '#E91E8C', // Magenta - Thymine
        C: '#8B5CF6', // Purple - Cytosine
        G: '#10B981'  // Green - Guanine
    };

    const nucleotides = ['A', 'T', 'C', 'G'];

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        initParticles();
    }

    function initParticles() {
        particles = [];
        const count = Math.floor((canvas.width * canvas.height) / 20000);

        for (let i = 0; i < count; i++) {
            const nucleotide = nucleotides[Math.floor(Math.random() * nucleotides.length)];
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 3 + 1,
                nucleotide: nucleotide,
                color: colors[nucleotide],
                alpha: Math.random() * 0.5 + 0.2
            });
        }
    }

    function drawParticle(particle) {
        ctx.save();
        ctx.globalAlpha = particle.alpha;
        ctx.fillStyle = particle.color;
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }

    function drawConnections() {
        const connectionDistance = 100;

        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < connectionDistance) {
                    const alpha = (1 - distance / connectionDistance) * 0.15;
                    ctx.save();
                    ctx.globalAlpha = alpha;
                    ctx.strokeStyle = particles[i].color;
                    ctx.lineWidth = 0.5;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                    ctx.restore();
                }
            }
        }
    }

    function updateParticles() {
        particles.forEach(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;

            // Wrap around edges
            if (particle.x < 0) particle.x = canvas.width;
            if (particle.x > canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = canvas.height;
            if (particle.y > canvas.height) particle.y = 0;
        });
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawConnections();
        particles.forEach(drawParticle);
        updateParticles();
        animationId = requestAnimationFrame(animate);
    }

    // Initialize
    resize();
    animate();

    // Handle resize
    window.addEventListener('resize', () => {
        resize();
    });
}

/**
 * Navigation functionality
 */
function initNavigation() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });

        // Close menu when clicking a link
        navMenu.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            });
        });
    }

    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 100) {
            navbar.style.background = 'rgba(10, 11, 20, 0.95)';
        } else {
            navbar.style.background = 'rgba(10, 11, 20, 0.8)';
        }

        lastScroll = currentScroll;
    });
}

/**
 * Demo Encoder functionality
 */
function initDemoEncoder() {
    const input = document.getElementById('demoInput');
    const output = document.getElementById('demoOutput');
    const encodeBtn = document.getElementById('demoEncode');
    const compressionRatio = document.getElementById('compressionRatio');
    const tabs = document.querySelectorAll('.demo-tab');

    // Quaternary encoding mapping
    const quaternaryMap = {
        '00': 'A',
        '01': 'T',
        '10': 'C',
        '11': 'G'
    };

    const reverseMap = {
        'A': '00',
        'T': '01',
        'C': '10',
        'G': '11'
    };

    let currentMode = 'encode';

    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentMode = tab.dataset.tab;

            if (currentMode === 'encode') {
                input.placeholder = 'Enter text to encode...';
                encodeBtn.querySelector('.btn-text').textContent = 'Convert to DNA';
            } else {
                input.placeholder = 'Enter DNA sequence (A, T, C, G)...';
                encodeBtn.querySelector('.btn-text').textContent = 'Decode to Text';
            }
        });
    });

    // Encode/Decode button click
    if (encodeBtn) {
        encodeBtn.addEventListener('click', () => {
            const inputValue = input.value.trim();
            if (!inputValue) {
                output.innerHTML = '<span class="dna-placeholder">Please enter some text</span>';
                return;
            }

            encodeBtn.classList.add('loading');

            // Simulate processing delay for effect
            setTimeout(() => {
                if (currentMode === 'encode') {
                    const result = encodeText(inputValue);
                    displayDNA(result);

                    // Calculate compression ratio
                    const originalBits = inputValue.length * 8;
                    const dnaBits = result.length * 2;
                    compressionRatio.textContent = `${(dnaBits / originalBits * 100).toFixed(1)}%`;
                } else {
                    const result = decodeDNA(inputValue);
                    output.innerHTML = `<span style="color: var(--text-primary);">${escapeHtml(result)}</span>`;
                    compressionRatio.textContent = '-';
                }

                encodeBtn.classList.remove('loading');
            }, 300);
        });
    }

    // Text to DNA encoding
    function encodeText(text) {
        let binary = '';

        // Convert text to binary
        for (let i = 0; i < text.length; i++) {
            const charCode = text.charCodeAt(i);
            binary += charCode.toString(2).padStart(8, '0');
        }

        // Convert binary to DNA (2 bits per nucleotide)
        let dna = '';
        for (let i = 0; i < binary.length; i += 2) {
            const bits = binary.substr(i, 2);
            dna += quaternaryMap[bits] || 'A';
        }

        return dna;
    }

    // DNA to text decoding
    function decodeDNA(dna) {
        // Clean input - only keep valid nucleotides
        dna = dna.toUpperCase().replace(/[^ATCG]/g, '');

        if (dna.length === 0) {
            return 'Invalid DNA sequence';
        }

        // Convert DNA to binary
        let binary = '';
        for (let i = 0; i < dna.length; i++) {
            binary += reverseMap[dna[i]] || '00';
        }

        // Convert binary to text
        let text = '';
        for (let i = 0; i < binary.length; i += 8) {
            const byte = binary.substr(i, 8);
            if (byte.length === 8) {
                const charCode = parseInt(byte, 2);
                if (charCode >= 32 && charCode <= 126) {
                    text += String.fromCharCode(charCode);
                } else if (charCode === 10 || charCode === 13) {
                    text += String.fromCharCode(charCode);
                } else {
                    text += '.';
                }
            }
        }

        return text || 'Could not decode sequence';
    }

    // Display DNA with colored nucleotides
    function displayDNA(dna) {
        let html = '';
        for (let i = 0; i < dna.length; i++) {
            const nucleotide = dna[i];
            const className = nucleotide.toLowerCase();
            html += `<span class="nucleotide ${className}">${nucleotide}</span>`;
        }
        output.innerHTML = html;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

/**
 * Code tabs functionality
 */
function initCodeTabs() {
    const tabs = document.querySelectorAll('.code-tab');
    const panels = document.querySelectorAll('.code-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const lang = tab.dataset.lang;

            // Update tabs
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update panels
            panels.forEach(panel => {
                panel.classList.remove('active');
                if (panel.id === `${lang}-panel`) {
                    panel.classList.add('active');
                }
            });
        });
    });
}

/**
 * Copy to clipboard functionality
 */
function initCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');

    copyButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const targetId = btn.dataset.target;
            let textToCopy = '';

            if (targetId) {
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    textToCopy = targetElement.textContent;
                }
            } else if (btn.id === 'copyInstall') {
                textToCopy = 'pip install vibedna';
            }

            if (textToCopy) {
                try {
                    await navigator.clipboard.writeText(textToCopy);
                    const originalText = btn.innerHTML;
                    btn.innerHTML = 'Copied!';
                    btn.style.color = 'var(--guanine)';

                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.style.color = '';
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy:', err);
                }
            }
        });
    });
}

/**
 * Scroll-triggered animations
 */
function initScrollAnimations() {
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements
    const animateElements = document.querySelectorAll(
        '.feature-card, .codec-card, .process-step, .arch-layer, .info-card'
    );

    animateElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    // Add CSS class for animation
    const style = document.createElement('style');
    style.textContent = `
        .animate-in {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);

    // Stagger animation for grid items
    document.querySelectorAll('.features-grid, .codecs-grid').forEach(grid => {
        const cards = grid.querySelectorAll('.feature-card, .codec-card');
        cards.forEach((card, index) => {
            card.style.transitionDelay = `${index * 0.1}s`;
        });
    });
}

/**
 * 3D Helix Animation
 */
function initHelixAnimation() {
    const container = document.getElementById('helixAnimation');
    if (!container) return;

    // Create a simple CSS-based helix visualization
    const helixHTML = `
        <div class="helix-wrapper">
            <div class="helix-strand strand-1"></div>
            <div class="helix-strand strand-2"></div>
            <div class="helix-bases">
                ${generateHelixBases(20)}
            </div>
        </div>
    `;

    container.innerHTML = helixHTML;

    function generateHelixBases(count) {
        const nucleotides = ['A', 'T', 'C', 'G'];
        let html = '';

        for (let i = 0; i < count; i++) {
            const left = nucleotides[Math.floor(Math.random() * nucleotides.length)];
            const right = getComplement(left);
            const delay = i * 0.1;

            html += `
                <div class="base-pair" style="--delay: ${delay}s; --index: ${i};">
                    <span class="base left ${left.toLowerCase()}">${left}</span>
                    <span class="base-connector"></span>
                    <span class="base right ${right.toLowerCase()}">${right}</span>
                </div>
            `;
        }

        return html;
    }

    function getComplement(nucleotide) {
        const complements = { 'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C' };
        return complements[nucleotide];
    }

    // Add helix styles
    const style = document.createElement('style');
    style.textContent = `
        .helix-wrapper {
            width: 200px;
            height: 400px;
            position: relative;
            perspective: 1000px;
        }

        .helix-bases {
            position: relative;
            width: 100%;
            height: 100%;
            transform-style: preserve-3d;
            animation: helixRotate 20s linear infinite;
        }

        @keyframes helixRotate {
            from { transform: rotateY(0deg); }
            to { transform: rotateY(360deg); }
        }

        .base-pair {
            position: absolute;
            left: 50%;
            transform: translateX(-50%) rotateY(calc(var(--index) * 36deg)) translateZ(60px);
            top: calc(var(--index) * 20px);
            display: flex;
            align-items: center;
            gap: 4px;
            animation: basePulse 2s ease-in-out infinite;
            animation-delay: var(--delay);
        }

        @keyframes basePulse {
            0%, 100% { opacity: 0.7; }
            50% { opacity: 1; }
        }

        .base {
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            font-size: 10px;
            font-weight: bold;
            font-family: 'JetBrains Mono', monospace;
        }

        .base.a { background: rgba(0, 212, 255, 0.3); color: #00D4FF; }
        .base.t { background: rgba(233, 30, 140, 0.3); color: #E91E8C; }
        .base.c { background: rgba(139, 92, 246, 0.3); color: #8B5CF6; }
        .base.g { background: rgba(16, 185, 129, 0.3); color: #10B981; }

        .base-connector {
            width: 20px;
            height: 2px;
            background: linear-gradient(90deg,
                rgba(255, 255, 255, 0.3) 0%,
                rgba(255, 255, 255, 0.1) 50%,
                rgba(255, 255, 255, 0.3) 100%
            );
        }
    `;
    document.head.appendChild(style);
}

/**
 * Smooth scroll for anchor links
 */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;

        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            e.preventDefault();
            const navHeight = document.querySelector('.navbar').offsetHeight;
            const targetPosition = targetElement.offsetTop - navHeight - 20;

            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

/**
 * Typing effect for hero subtitle (optional enhancement)
 */
function initTypingEffect() {
    const subtitle = document.querySelector('.hero-subtitle');
    if (!subtitle) return;

    const text = subtitle.textContent;
    subtitle.textContent = '';
    subtitle.style.borderRight = '2px solid var(--cyan)';

    let i = 0;
    function type() {
        if (i < text.length) {
            subtitle.textContent += text.charAt(i);
            i++;
            setTimeout(type, 30);
        } else {
            subtitle.style.borderRight = 'none';
        }
    }

    // Start typing after a delay
    setTimeout(type, 1000);
}

/**
 * Counter animation for stats
 */
function animateCounters() {
    const counters = document.querySelectorAll('.stat-value');

    counters.forEach(counter => {
        const target = counter.textContent;
        const isNumber = /^\d+$/.test(target);

        if (isNumber) {
            const targetNum = parseInt(target);
            let current = 0;
            const increment = targetNum / 50;
            const duration = 1500;
            const stepTime = duration / 50;

            const updateCounter = () => {
                current += increment;
                if (current < targetNum) {
                    counter.textContent = Math.ceil(current);
                    setTimeout(updateCounter, stepTime);
                } else {
                    counter.textContent = targetNum;
                }
            };

            // Use Intersection Observer to trigger animation
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        updateCounter();
                        observer.unobserve(counter);
                    }
                });
            }, { threshold: 0.5 });

            observer.observe(counter);
        }
    });
}

// Initialize counter animation after DOM load
document.addEventListener('DOMContentLoaded', animateCounters);

/**
 * Parallax effect for hero section
 */
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const hero = document.querySelector('.hero-content');

    if (hero && scrolled < window.innerHeight) {
        hero.style.transform = `translateY(${scrolled * 0.3}px)`;
        hero.style.opacity = 1 - (scrolled / window.innerHeight);
    }
});

// © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
