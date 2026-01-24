/**
 * =============================================================================
 * CROP YIELD DATA STORAGE - ADVANCED JAVASCRIPT
 * Enterprise-grade features with smooth animations and interactions
 * =============================================================================
 */

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Debounce function to limit the rate of function execution
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func.apply(this, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(this, args);
    };
}

/**
 * Throttle function to ensure a function is called at most once in a specified period
 */
function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Check if element is in viewport
 */
function isInViewport(element, offset = 0) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top <= (window.innerHeight || document.documentElement.clientHeight) - offset &&
        rect.bottom >= 0
    );
}

/**
 * Smooth scroll to element
 */
function smoothScrollTo(element, offset = 80) {
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;
    
    window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
    });
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Animate number counter
 */
function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16);
    const isDecimal = String(target).includes('.');
    
    function updateCounter() {
        start += increment;
        if (start < target) {
            if (isDecimal) {
                element.textContent = start.toFixed(1);
            } else {
                element.textContent = Math.floor(start);
            }
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent = target;
        }
    }
    
    requestAnimationFrame(updateCounter);
}

// =============================================================================
// NAVIGATION
// =============================================================================

class Navigation {
    constructor() {
        this.navbar = document.getElementById('navbar');
        this.navToggle = document.getElementById('navToggle');
        this.navMenu = document.getElementById('navMenu');
        this.lastScrollTop = 0;
        this.scrollThreshold = 100;
        
        this.init();
    }
    
    init() {
        // Mobile menu toggle
        if (this.navToggle) {
            this.navToggle.addEventListener('click', () => this.toggleMobileMenu());
        }
        
        // Close menu on link click
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => this.closeMobileMenu());
        });
        
        // Close menu on outside click
        document.addEventListener('click', (e) => {
            if (!this.navMenu?.contains(e.target) && !this.navToggle?.contains(e.target)) {
                this.closeMobileMenu();
            }
        });
        
        // Scroll behavior
        window.addEventListener('scroll', throttle(() => this.handleScroll(), 100));
        
        // Handle initial state
        this.handleScroll();
    }
    
    toggleMobileMenu() {
        this.navToggle.classList.toggle('active');
        this.navMenu.classList.toggle('active');
        document.body.style.overflow = this.navMenu.classList.contains('active') ? 'hidden' : '';
    }
    
    closeMobileMenu() {
        this.navToggle?.classList.remove('active');
        this.navMenu?.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    handleScroll() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Add scrolled class
        if (scrollTop > this.scrollThreshold) {
            this.navbar?.classList.add('scrolled');
        } else {
            this.navbar?.classList.remove('scrolled');
        }
        
        this.lastScrollTop = scrollTop;
    }
}

// =============================================================================
// SCROLL ANIMATIONS (AOS-like)
// =============================================================================

class ScrollAnimations {
    constructor() {
        this.elements = document.querySelectorAll('[data-aos]');
        this.defaultOffset = 100;
        
        this.init();
    }
    
    init() {
        if (this.elements.length === 0) return;
        
        // Check elements on load
        this.checkElements();
        
        // Check elements on scroll
        window.addEventListener('scroll', throttle(() => this.checkElements(), 100));
        
        // Check elements on resize
        window.addEventListener('resize', debounce(() => this.checkElements(), 200));
    }
    
    checkElements() {
        this.elements.forEach(element => {
            const delay = parseInt(element.dataset.aosDelay) || 0;
            
            if (isInViewport(element, this.defaultOffset)) {
                setTimeout(() => {
                    element.classList.add('aos-animate');
                }, delay);
            }
        });
    }
}

// =============================================================================
// FLASH MESSAGES
// =============================================================================

class FlashMessages {
    constructor() {
        this.container = document.querySelector('.flash-container');
        this.autoHideDelay = 5000;
        
        this.init();
    }
    
    init() {
        if (!this.container) return;
        
        const messages = this.container.querySelectorAll('.flash-message');
        messages.forEach((message, index) => {
            // Animate in with stagger
            message.style.animationDelay = `${index * 0.1}s`;
            
            // Auto hide
            setTimeout(() => {
                this.hideMessage(message);
            }, this.autoHideDelay + (index * 500));
        });
    }
    
    hideMessage(message) {
        message.style.animation = 'slideOutRight 0.5s ease forwards';
        setTimeout(() => {
            message.remove();
            
            // Remove container if empty
            if (this.container && this.container.children.length === 0) {
                this.container.remove();
            }
        }, 500);
    }
    
    // Static method to show new flash message
    static show(message, type = 'info') {
        let container = document.querySelector('.flash-container');
        
        if (!container) {
            container = document.createElement('div');
            container.className = 'flash-container';
            document.body.appendChild(container);
        }
        
        const icons = {
            success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22,4 12,14.01 9,11.01"/></svg>',
            error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
        };
        
        const flashEl = document.createElement('div');
        flashEl.className = `flash-message flash-${type}`;
        flashEl.innerHTML = `
            <div class="flash-icon">${icons[type] || icons.info}</div>
            <span class="flash-text">${message}</span>
            <button class="flash-close" onclick="this.parentElement.remove()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        `;
        
        container.appendChild(flashEl);
        
        // Auto remove after delay
        setTimeout(() => {
            flashEl.style.animation = 'slideOutRight 0.5s ease forwards';
            setTimeout(() => flashEl.remove(), 500);
        }, 5000);
    }
}

// Add CSS for slideOutRight animation if not exists
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(styleSheet);

// =============================================================================
// AUTH TABS
// =============================================================================

class AuthTabs {
    constructor() {
        this.tabs = document.querySelectorAll('.auth-tab');
        this.forms = document.querySelectorAll('.auth-form-container');
        this.indicator = document.querySelector('.tab-indicator');
        this.switchButtons = document.querySelectorAll('.switch-form');
        
        this.init();
    }
    
    init() {
        if (this.tabs.length === 0) return;
        
        // Tab click handlers
        this.tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                this.switchTab(target);
            });
        });
        
        // Switch form buttons
        this.switchButtons.forEach(button => {
            button.addEventListener('click', () => {
                const target = button.dataset.target;
                this.switchTab(target);
            });
        });
    }
    
    switchTab(target) {
        // Update tabs
        this.tabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === target);
        });
        
        // Update forms
        this.forms.forEach(form => {
            const formId = form.id.toLowerCase();
            const isActive = formId.includes(target);
            form.classList.toggle('active', isActive);
        });
        
        // Update indicator position
        if (this.indicator) {
            this.indicator.style.transform = target === 'signup' ? 'translateX(100%)' : 'translateX(0)';
        }
    }
}

// =============================================================================
// PASSWORD VISIBILITY TOGGLE
// =============================================================================

class PasswordToggle {
    constructor() {
        this.toggleButtons = document.querySelectorAll('.toggle-password');
        
        this.init();
    }
    
    init() {
        this.toggleButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggle(button);
            });
        });
    }
    
    toggle(button) {
        const targetId = button.dataset.target;
        const input = document.getElementById(targetId);
        const eyeOpen = button.querySelector('.eye-open');
        const eyeClosed = button.querySelector('.eye-closed');
        
        if (input) {
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            
            if (eyeOpen && eyeClosed) {
                eyeOpen.style.display = isPassword ? 'none' : 'block';
                eyeClosed.style.display = isPassword ? 'block' : 'none';
            }
        }
    }
}

// =============================================================================
// PASSWORD STRENGTH METER
// =============================================================================

class PasswordStrength {
    constructor() {
        this.passwordInputs = document.querySelectorAll('input[type="password"]');
        
        this.init();
    }
    
    init() {
        this.passwordInputs.forEach(input => {
            const strengthContainer = input.closest('.form-group')?.querySelector('.password-strength');
            
            if (strengthContainer) {
                input.addEventListener('input', () => {
                    this.updateStrength(input.value, strengthContainer);
                });
            }
        });
    }
    
    updateStrength(password, container) {
        const fill = container.querySelector('.strength-fill');
        const text = container.querySelector('.strength-text');
        
        if (!fill || !text) return;
        
        const strength = this.calculateStrength(password);
        
        fill.className = 'strength-fill';
        
        if (password.length === 0) {
            fill.style.width = '0';
            text.textContent = 'Password strength';
        } else if (strength < 2) {
            fill.classList.add('weak');
            text.textContent = 'Weak password';
        } else if (strength < 4) {
            fill.classList.add('medium');
            text.textContent = 'Medium strength';
        } else {
            fill.classList.add('strong');
            text.textContent = 'Strong password';
        }
    }
    
    calculateStrength(password) {
        let strength = 0;
        
        if (password.length >= 6) strength++;
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[^a-zA-Z0-9]/.test(password)) strength++;
        
        return strength;
    }
}

// =============================================================================
// FORM VALIDATION
// =============================================================================

class FormValidation {
    constructor() {
        this.forms = document.querySelectorAll('.auth-form, .yield-form');
        
        this.init();
    }
    
    init() {
        this.forms.forEach(form => {
            // Real-time validation
            form.querySelectorAll('input, select').forEach(input => {
                input.addEventListener('blur', () => this.validateField(input));
                input.addEventListener('input', () => this.clearError(input));
            });
            
            // Form submission
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });
        });
    }
    
    validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        const name = field.name;
        const required = field.hasAttribute('required');
        const minLength = field.getAttribute('minlength');
        
        let error = '';
        
        // Required check
        if (required && !value) {
            error = 'This field is required';
        }
        
        // Email validation
        else if (type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                error = 'Please enter a valid email address';
            }
        }
        
        // Password validation
        else if (type === 'password' && value) {
            if (minLength && value.length < parseInt(minLength)) {
                error = `Password must be at least ${minLength} characters`;
            }
        }
        
        // Number validation
        else if (type === 'number' && value) {
            const num = parseFloat(value);
            if (isNaN(num) || num <= 0) {
                error = 'Please enter a valid positive number';
            }
        }
        
        // Name validation
        else if (name === 'name' && value) {
            if (value.length < 2) {
                error = 'Name must be at least 2 characters';
            }
        }
        
        this.showError(field, error);
        return !error;
    }
    
    validateForm(form) {
        let isValid = true;
        
        form.querySelectorAll('input[required], select[required]').forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    showError(field, message) {
        const errorElement = field.closest('.form-group')?.querySelector('.error-message');
        
        if (errorElement) {
            errorElement.textContent = message;
        }
        
        if (message) {
            field.style.borderColor = 'var(--error)';
        } else {
            field.style.borderColor = '';
        }
    }
    
    clearError(field) {
        const errorElement = field.closest('.form-group')?.querySelector('.error-message');
        
        if (errorElement) {
            errorElement.textContent = '';
        }
        
        field.style.borderColor = '';
    }
}

// =============================================================================
// TABLE SEARCH & SORT
// =============================================================================

class TableManager {
    constructor(tableId, searchId) {
        this.table = document.getElementById(tableId);
        this.searchInput = document.getElementById(searchId);
        this.sortDirection = {};
        
        this.init();
    }
    
    init() {
        if (!this.table) return;
        
        // Search functionality
        if (this.searchInput) {
            this.searchInput.addEventListener('input', debounce(() => {
                this.search(this.searchInput.value);
            }, 300));
        }
        
        // Sort functionality
        const sortableHeaders = this.table.querySelectorAll('th.sortable');
        sortableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const sortKey = header.dataset.sort;
                this.sort(sortKey);
            });
        });
    }
    
    search(query) {
        const rows = this.table.querySelectorAll('tbody tr');
        const lowerQuery = query.toLowerCase();
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const isVisible = text.includes(lowerQuery);
            row.style.display = isVisible ? '' : 'none';
            
            // Add highlight animation for visible rows
            if (isVisible && query) {
                row.style.animation = 'none';
                row.offsetHeight; // Trigger reflow
                row.style.animation = 'highlight 0.5s ease';
            }
        });
        
        // Update pagination info
        this.updatePaginationInfo();
    }
    
    sort(key) {
        const tbody = this.table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        // Toggle sort direction
        this.sortDirection[key] = this.sortDirection[key] === 'asc' ? 'desc' : 'asc';
        const direction = this.sortDirection[key];
        
        // Get column index
        const headers = Array.from(this.table.querySelectorAll('th'));
        const columnIndex = headers.findIndex(h => h.dataset.sort === key);
        
        if (columnIndex === -1) return;
        
        // Sort rows
        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex].textContent.trim();
            const bValue = b.cells[columnIndex].textContent.trim();
            
            // Try numeric comparison
            const aNum = parseFloat(aValue);
            const bNum = parseFloat(bValue);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return direction === 'asc' ? aNum - bNum : bNum - aNum;
            }
            
            // String comparison
            return direction === 'asc' 
                ? aValue.localeCompare(bValue)
                : bValue.localeCompare(aValue);
        });
        
        // Re-append rows
        rows.forEach(row => tbody.appendChild(row));
        
        // Update header icons
        this.updateSortIcons(key, direction);
    }
    
    updateSortIcons(activeKey, direction) {
        const headers = this.table.querySelectorAll('th.sortable');
        
        headers.forEach(header => {
            const icon = header.querySelector('svg');
            if (icon) {
                if (header.dataset.sort === activeKey) {
                    icon.style.transform = direction === 'desc' ? 'rotate(180deg)' : '';
                    icon.style.opacity = '1';
                } else {
                    icon.style.transform = '';
                    icon.style.opacity = '0.5';
                }
            }
        });
    }
    
    updatePaginationInfo() {
        const visibleRows = this.table.querySelectorAll('tbody tr:not([style*="display: none"])');
        const totalRows = this.table.querySelectorAll('tbody tr');
        const infoEl = document.querySelector('.pagination-info');
        
        if (infoEl) {
            const spans = infoEl.querySelectorAll('span');
            if (spans.length >= 2) {
                spans[0].textContent = visibleRows.length;
                spans[1].textContent = totalRows.length;
            }
        }
    }
}

// Add highlight animation
const highlightStyle = document.createElement('style');
highlightStyle.textContent = `
    @keyframes highlight {
        0% { background-color: var(--primary-100); }
        100% { background-color: transparent; }
    }
`;
document.head.appendChild(highlightStyle);

// =============================================================================
// COUNTER ANIMATION
// =============================================================================

class CounterAnimation {
    constructor() {
        this.counters = document.querySelectorAll('[data-count]');
        this.animated = new Set();
        
        this.init();
    }
    
    init() {
        if (this.counters.length === 0) return;
        
        // Check on load
        this.checkCounters();
        
        // Check on scroll
        window.addEventListener('scroll', throttle(() => this.checkCounters(), 100));
    }
    
    checkCounters() {
        this.counters.forEach(counter => {
            if (!this.animated.has(counter) && isInViewport(counter, 100)) {
                this.animated.add(counter);
                const target = counter.dataset.count;
                animateCounter(counter, parseFloat(target));
            }
        });
    }
}

// =============================================================================
// SMOOTH SCROLL
// =============================================================================

class SmoothScroll {
    constructor() {
        this.init();
    }
    
    init() {
        // Handle anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                const targetId = anchor.getAttribute('href');
                
                if (targetId === '#') return;
                
                const target = document.querySelector(targetId);
                
                if (target) {
                    e.preventDefault();
                    smoothScrollTo(target);
                }
            });
        });
    }
}

// =============================================================================
// LOADING STATES
// =============================================================================

class LoadingState {
    static show(button) {
        if (!button) return;
        
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `
            <svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px; animation: spin 1s linear infinite;">
                <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
            </svg>
            <span>Processing...</span>
        `;
    }
    
    static hide(button) {
        if (!button || !button.dataset.originalText) return;
        
        button.disabled = false;
        button.innerHTML = button.dataset.originalText;
        delete button.dataset.originalText;
    }
}

// Add spinner animation
const spinnerStyle = document.createElement('style');
spinnerStyle.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(spinnerStyle);

// =============================================================================
// PARALLAX EFFECTS
// =============================================================================

class ParallaxEffects {
    constructor() {
        this.elements = document.querySelectorAll('.floating-shape');
        
        this.init();
    }
    
    init() {
        if (this.elements.length === 0) return;
        
        window.addEventListener('scroll', throttle(() => this.update(), 50));
    }
    
    update() {
        const scrollY = window.pageYOffset;
        
        this.elements.forEach((element, index) => {
            const speed = 0.05 + (index * 0.02);
            const yPos = scrollY * speed;
            element.style.transform = `translateY(${yPos}px)`;
        });
    }
}

// =============================================================================
// RIPPLE EFFECT
// =============================================================================

class RippleEffect {
    constructor() {
        this.buttons = document.querySelectorAll('.btn');
        
        this.init();
    }
    
    init() {
        this.buttons.forEach(button => {
            button.addEventListener('click', (e) => this.createRipple(e, button));
        });
    }
    
    createRipple(event, button) {
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
        `;
        
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    }
}

// Add ripple animation
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(rippleStyle);

// =============================================================================
// TYPING EFFECT
// =============================================================================

class TypingEffect {
    constructor(element, texts, speed = 100) {
        this.element = element;
        this.texts = texts;
        this.speed = speed;
        this.textIndex = 0;
        this.charIndex = 0;
        this.isDeleting = false;
        
        if (this.element) {
            this.type();
        }
    }
    
    type() {
        const currentText = this.texts[this.textIndex];
        
        if (this.isDeleting) {
            this.element.textContent = currentText.substring(0, this.charIndex - 1);
            this.charIndex--;
        } else {
            this.element.textContent = currentText.substring(0, this.charIndex + 1);
            this.charIndex++;
        }
        
        let typeSpeed = this.speed;
        
        if (this.isDeleting) {
            typeSpeed /= 2;
        }
        
        if (!this.isDeleting && this.charIndex === currentText.length) {
            typeSpeed = 2000; // Pause at end
            this.isDeleting = true;
        } else if (this.isDeleting && this.charIndex === 0) {
            this.isDeleting = false;
            this.textIndex = (this.textIndex + 1) % this.texts.length;
            typeSpeed = 500; // Pause before typing next
        }
        
        setTimeout(() => this.type(), typeSpeed);
    }
}

// =============================================================================
// TOOLTIP
// =============================================================================

class Tooltip {
    constructor() {
        this.elements = document.querySelectorAll('[data-tooltip]');
        
        this.init();
    }
    
    init() {
        this.elements.forEach(element => {
            element.addEventListener('mouseenter', (e) => this.show(e, element));
            element.addEventListener('mouseleave', () => this.hide());
        });
    }
    
    show(event, element) {
        const text = element.dataset.tooltip;
        
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            position: fixed;
            background: var(--gray-900);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            z-index: 10000;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
        `;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        tooltip.style.left = `${rect.left + rect.width / 2 - tooltipRect.width / 2}px`;
        tooltip.style.top = `${rect.top - tooltipRect.height - 8}px`;
        
        requestAnimationFrame(() => {
            tooltip.style.opacity = '1';
        });
    }
    
    hide() {
        const tooltip = document.querySelector('.tooltip');
        if (tooltip) {
            tooltip.style.opacity = '0';
            setTimeout(() => tooltip.remove(), 200);
        }
    }
}

// =============================================================================
// THEME MANAGER (Dark Mode Support)
// =============================================================================

class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.init();
    }
    
    init() {
        this.setTheme(this.theme);
        
        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
    
    setTheme(theme) {
        this.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }
    
    toggle() {
        this.setTheme(this.theme === 'light' ? 'dark' : 'light');
    }
}

// =============================================================================
// LOCAL STORAGE MANAGER
// =============================================================================

class StorageManager {
    static set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.warn('LocalStorage not available:', e);
            return false;
        }
    }
    
    static get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.warn('LocalStorage not available:', e);
            return defaultValue;
        }
    }
    
    static remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.warn('LocalStorage not available:', e);
            return false;
        }
    }
}

// =============================================================================
// EXPORT CSV
// =============================================================================

class ExportManager {
    static toCSV(tableId, filename = 'export.csv') {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        const rows = Array.from(table.querySelectorAll('tr'));
        const csvContent = rows.map(row => {
            const cells = Array.from(row.querySelectorAll('th, td'));
            return cells.map(cell => {
                let text = cell.textContent.trim();
                // Escape quotes and wrap in quotes if contains comma
                if (text.includes(',') || text.includes('"')) {
                    text = `"${text.replace(/"/g, '""')}"`;
                }
                return text;
            }).join(',');
        }).join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
        
        FlashMessages.show('Data exported successfully!', 'success');
    }
}

// Add export button functionality
document.addEventListener('DOMContentLoaded', () => {
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            ExportManager.toCSV('allYieldsTable', 'crop_yields_data.csv');
        });
    }
});

// =============================================================================
// PRINT FUNCTIONALITY
// =============================================================================

class PrintManager {
    static print() {
        window.print();
    }
    
    static printSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (!section) return;
        
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Print</title>
                    <link rel="stylesheet" href="/static/css/style.css">
                </head>
                <body>
                    ${section.outerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}

// =============================================================================
// KEYBOARD SHORTCUTS
// =============================================================================

class KeyboardShortcuts {
    constructor() {
        this.init();
    }
    
    init() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search focus
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('.search-box input');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // Escape to close modals/menus
            if (e.key === 'Escape') {
                const navMenu = document.getElementById('navMenu');
                if (navMenu?.classList.contains('active')) {
                    document.getElementById('navToggle')?.click();
                }
            }
        });
    }
}

// =============================================================================
// INITIALIZE ALL COMPONENTS
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Core components
    new Navigation();
    new ScrollAnimations();
    new FlashMessages();
    new SmoothScroll();
    new ParallaxEffects();
    new RippleEffect();
    new KeyboardShortcuts();
    
    // Auth components
    new AuthTabs();
    new PasswordToggle();
    new PasswordStrength();
    new FormValidation();
    
    // Dashboard components
    new TableManager('yieldsTable', 'searchRecords');
    new TableManager('usersTable', 'searchUsers');
    new TableManager('allYieldsTable', 'searchYields');
    new CounterAnimation();
    new Tooltip();
    
    // Log initialization
    console.log('AgriCloud JS initialized successfully');
});

// =============================================================================
// GLOBAL EXPORTS
// =============================================================================

window.FlashMessages = FlashMessages;
window.LoadingState = LoadingState;
window.ExportManager = ExportManager;
window.PrintManager = PrintManager;
window.StorageManager = StorageManager;
