/**
 * MySQL to Sheets Dashboard - Shared JavaScript Utilities
 * Provides common functionality for all dashboard pages
 */

/* ==========================================================================
   CSRF Protection - Auto-inject token into all state-changing fetch requests
   ========================================================================== */

(function() {
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        options = options || {};
        const method = (options.method || 'GET').toUpperCase();
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
            const token = document.querySelector('meta[name="csrf-token"]');
            if (token) {
                options.headers = options.headers || {};
                if (options.headers instanceof Headers) {
                    if (!options.headers.has('X-CSRFToken')) {
                        options.headers.set('X-CSRFToken', token.content);
                    }
                } else {
                    options.headers['X-CSRFToken'] = options.headers['X-CSRFToken'] || token.content;
                }
            }
        }
        return originalFetch.call(this, url, options);
    };
})();

/* ==========================================================================
   Alert System
   ========================================================================== */

/**
 * Show an alert message in the specified container
 * @param {string|Object} messageOrError - Message string or error object with message/remediation
 * @param {string} type - Alert type: 'success', 'error', 'warning', 'info'
 * @param {string} containerId - ID of the alert container (default: 'alertContainer')
 * @param {number} timeout - Auto-hide timeout in ms (default: 5000, 0 to disable)
 */
function showAlert(messageOrError, type = 'success', containerId = 'alertContainer', timeout = 5000) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Alert container '${containerId}' not found`);
        return;
    }

    let message = '';
    let remediation = '';

    // Handle error objects with remediation hints
    if (typeof messageOrError === 'object' && messageOrError !== null) {
        message = messageOrError.message || messageOrError.error || 'An error occurred';
        remediation = messageOrError.remediation || '';

        // Check for error code
        if (messageOrError.code || messageOrError.error_code) {
            const code = messageOrError.code || messageOrError.error_code;
            message = `[${code}] ${message}`;
        }
    } else {
        message = String(messageOrError);
    }

    // Build alert HTML
    let alertHtml = `<div class="alert alert-${type}">`;
    alertHtml += `<div class="alert-message">${escapeHtml(message)}</div>`;

    // Add remediation hint for errors
    if (remediation && type === 'error') {
        alertHtml += `<div class="alert-remediation" style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(0,0,0,0.1); font-size: 0.8125rem;">`;
        alertHtml += `<strong>Fix:</strong> ${escapeHtml(remediation)}`;
        alertHtml += `</div>`;
    }

    alertHtml += `</div>`;
    container.innerHTML = alertHtml;
    container.style.display = 'block';

    if (timeout > 0) {
        setTimeout(() => {
            container.innerHTML = '';
            container.style.display = 'none';
        }, timeout);
    }
}

/**
 * Show an error with remediation from an API response
 * @param {Object} response - API response object
 * @param {string} containerId - ID of the alert container
 */
function showApiError(response, containerId = 'alertContainer') {
    const errorData = {
        message: response.message || response.error || 'An error occurred',
        code: response.error_code || response.code,
        remediation: response.remediation,
    };
    showAlert(errorData, 'error', containerId, 0); // No auto-hide for errors
}

/**
 * Hide the alert in the specified container
 * @param {string} containerId - ID of the alert container
 */
function hideAlert(containerId = 'alertContainer') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
        container.style.display = 'none';
    }
}

/* ==========================================================================
   Loading States
   ========================================================================== */

/**
 * Set loading state on a button
 * @param {HTMLButtonElement} button - The button element
 * @param {boolean} loading - Whether to show loading state
 * @param {string} loadingText - Text to show while loading (default: 'Processing...')
 */
function setButtonLoading(button, loading, loadingText = 'Processing...') {
    if (!button) return;

    if (loading) {
        button.disabled = true;
        button._originalText = button.textContent;
        button.innerHTML = `<span class="loading"></span>${escapeHtml(loadingText)}`;
    } else {
        button.disabled = false;
        button.textContent = button._originalText || button.textContent;
    }
}

/* ==========================================================================
   Fetch Wrapper
   ========================================================================== */

/**
 * Wrapper around fetch with common options and error handling
 * @param {string} url - Request URL
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} - Parsed JSON response
 */
async function apiFetch(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, mergedOptions);

        // Handle non-JSON responses
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return { success: true };
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || data.error || `HTTP ${response.status}`);
        }

        return data;
    } catch (error) {
        if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
            throw new Error('Network error: Unable to connect to server');
        }
        throw error;
    }
}

/**
 * POST request with JSON body
 * @param {string} url - Request URL
 * @param {Object} data - Request body
 * @returns {Promise<Object>} - Parsed JSON response
 */
async function apiPost(url, data) {
    return apiFetch(url, {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

/**
 * PUT request with JSON body
 * @param {string} url - Request URL
 * @param {Object} data - Request body
 * @returns {Promise<Object>} - Parsed JSON response
 */
async function apiPut(url, data) {
    return apiFetch(url, {
        method: 'PUT',
        body: JSON.stringify(data),
    });
}

/**
 * DELETE request
 * @param {string} url - Request URL
 * @returns {Promise<Object>} - Parsed JSON response
 */
async function apiDelete(url) {
    return apiFetch(url, {
        method: 'DELETE',
    });
}

/* ==========================================================================
   Modal Utilities
   ========================================================================== */

/**
 * Open a modal by ID
 * @param {string} modalId - The modal element ID
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Close a modal by ID
 * @param {string} modalId - The modal element ID
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';

        // Reset any forms within the modal
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
}

/**
 * Initialize modal close behaviors for all modals on the page
 */
function initModals() {
    // Close on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => {
                closeModal(modal.id);
            });
        }
    });
}

/* ==========================================================================
   Utility Functions
   ========================================================================== */

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format a date string for display
 * @param {string} dateStr - ISO date string
 * @returns {string} - Formatted date
 */
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
        const date = new Date(dateStr);
        return date.toLocaleString();
    } catch {
        return dateStr;
    }
}

/**
 * Format a number with commas
 * @param {number} num - Number to format
 * @returns {string} - Formatted number
 */
function formatNumber(num) {
    if (typeof num !== 'number') return num;
    return num.toLocaleString();
}

/**
 * Truncate text with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} - Truncated text
 */
function truncate(text, maxLength = 50) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Debounce a function
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} - Debounced function
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} - Success status
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            return true;
        } catch {
            return false;
        } finally {
            document.body.removeChild(textarea);
        }
    }
}

/**
 * Confirm action with a dialog
 * @param {string} message - Confirmation message
 * @returns {boolean} - User's choice
 */
function confirmAction(message) {
    return window.confirm(message);
}

/* ==========================================================================
   Form Utilities
   ========================================================================== */

/**
 * Get form data as an object
 * @param {HTMLFormElement} form - The form element
 * @returns {Object} - Form data as key-value pairs
 */
function getFormData(form) {
    const formData = new FormData(form);
    const data = {};

    for (const [key, value] of formData.entries()) {
        // Handle checkboxes
        const input = form.querySelector(`[name="${key}"]`);
        if (input && input.type === 'checkbox') {
            data[key] = input.checked;
        } else if (input && input.type === 'number') {
            data[key] = value ? Number(value) : null;
        } else {
            data[key] = value || null;
        }
    }

    return data;
}

/**
 * Populate form fields from an object
 * @param {HTMLFormElement} form - The form element
 * @param {Object} data - Data to populate
 */
function populateForm(form, data) {
    Object.entries(data).forEach(([key, value]) => {
        const input = form.querySelector(`[name="${key}"]`);
        if (!input) return;

        if (input.type === 'checkbox') {
            input.checked = Boolean(value);
        } else if (value !== null && value !== undefined) {
            input.value = value;
        }
    });
}

/* ==========================================================================
   Page Loading Bar
   ========================================================================== */

/**
 * Page loading bar for navigation feedback
 */
const PageLoadingBar = {
    element: null,

    init() {
        // Create loading bar element
        const bar = document.createElement('div');
        bar.className = 'page-loading-bar';
        bar.innerHTML = '<div class="bar"></div>';
        document.body.prepend(bar);
        this.element = bar;

        // Intercept link clicks
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link &&
                link.href &&
                !link.target &&
                !link.hasAttribute('download') &&
                link.origin === window.location.origin &&
                !link.href.includes('#') &&
                !e.ctrlKey && !e.metaKey && !e.shiftKey) {
                this.start();
            }
        });

        // Stop on page load
        window.addEventListener('pageshow', () => this.complete());
    },

    start() {
        if (this.element) {
            this.element.classList.remove('complete');
            this.element.classList.add('loading');
        }
    },

    complete() {
        if (this.element) {
            this.element.classList.remove('loading');
            this.element.classList.add('complete');
            setTimeout(() => {
                this.element.classList.remove('complete');
            }, 500);
        }
    }
};

/* ==========================================================================
   Search Input Auto-Debounce
   ========================================================================== */

/**
 * Auto-initialize debounce on search inputs
 */
function initSearchDebounce() {
    // Find all search inputs
    const searchInputs = document.querySelectorAll(
        'input[type="search"], input[data-debounce], .search-input'
    );

    searchInputs.forEach(input => {
        if (input._debounceInitialized) return;

        const wait = parseInt(input.dataset.debounceWait) || 300;
        const originalHandler = input.oninput;

        input.addEventListener('input', debounce((e) => {
            // Remove debouncing visual
            input.classList.remove('debouncing');

            // Call original handler if exists
            if (originalHandler) {
                originalHandler.call(input, e);
            }
        }, wait));

        // Add debouncing visual feedback
        input.addEventListener('input', () => {
            input.classList.add('debouncing');
        }, { capture: true });

        input._debounceInitialized = true;
    });
}

/* ==========================================================================
   Sidebar Navigation
   ========================================================================== */

/**
 * Sidebar controller for collapse/expand and mobile behavior
 */
const Sidebar = {
    STORAGE_KEY: 'sidebar_collapsed',

    init() {
        this.sidebar = document.getElementById('sidebar');
        this.toggle = document.getElementById('sidebarToggle');
        this.mobileToggle = document.getElementById('mobileNavToggle');
        this.overlay = document.getElementById('sidebarOverlay');
        this.body = document.getElementById('appBody');

        if (!this.sidebar) return;

        // Restore collapsed state from localStorage
        const collapsed = localStorage.getItem(this.STORAGE_KEY) === 'true';
        if (collapsed) {
            this.sidebar.classList.add('collapsed');
            this.body?.classList.add('sidebar-collapsed');
        }

        // Desktop collapse toggle
        this.toggle?.addEventListener('click', () => this.toggleCollapse());

        // Mobile hamburger toggle
        this.mobileToggle?.addEventListener('click', () => this.toggleMobile());

        // Close mobile sidebar on overlay click
        this.overlay?.addEventListener('click', () => this.closeMobile());

        // Keyboard shortcut: Cmd/Ctrl + \ to toggle sidebar
        document.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === '\\') {
                e.preventDefault();
                if (window.innerWidth < 1024) {
                    this.toggleMobile();
                } else {
                    this.toggleCollapse();
                }
            }
        });

        // Close mobile sidebar on window resize to desktop
        window.addEventListener('resize', debounce(() => {
            if (window.innerWidth >= 1024) {
                this.closeMobile();
            }
        }, 100));
    },

    toggleCollapse() {
        if (!this.sidebar) return;

        const isCollapsed = this.sidebar.classList.toggle('collapsed');
        this.body?.classList.toggle('sidebar-collapsed', isCollapsed);

        // Update toggle icon direction
        const icon = this.toggle?.querySelector('svg');
        if (icon) {
            icon.style.transform = isCollapsed ? 'rotate(180deg)' : '';
        }

        // Save preference
        localStorage.setItem(this.STORAGE_KEY, isCollapsed);
    },

    toggleMobile() {
        if (!this.sidebar) return;

        const isOpen = this.sidebar.classList.toggle('mobile-open');
        this.overlay?.classList.toggle('active', isOpen);
        document.body.style.overflow = isOpen ? 'hidden' : '';
    },

    closeMobile() {
        this.sidebar?.classList.remove('mobile-open');
        this.overlay?.classList.remove('active');
        document.body.style.overflow = '';
    }
};

/* ==========================================================================
   Initialization
   ========================================================================== */

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initModals();
    PageLoadingBar.init();
    initSearchDebounce();
    Sidebar.init();
});
