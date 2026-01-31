/**
 * Keyboard shortcuts for the dashboard.
 * Press ? to show help modal.
 *
 * Shortcuts:
 * - ? : Show shortcuts help
 * - / : Focus search
 * - g h : Go to Dashboard
 * - g c : Go to Configs
 * - g s : Go to Schedules
 * - g j : Go to Jobs
 * - g f : Go to Freshness
 * - g d : Go to Diagnostics
 * - Escape : Close modal/dropdown
 * - Cmd/Ctrl + K : Quick search (if available)
 * - Cmd/Ctrl + S : Save form (if applicable)
 * - Cmd/Ctrl + Enter : Run sync (on dashboard)
 */
class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map([
            ['?', { description: 'Show shortcuts help', handler: () => this.showHelp() }],
            ['/', { description: 'Focus search', handler: () => this.focusSearch() }],
            ['g h', { description: 'Go to Dashboard', handler: () => this.navigate('/') }],
            ['g c', { description: 'Go to Configs', handler: () => this.navigate('/configs') }],
            ['g s', { description: 'Go to Schedules', handler: () => this.navigate('/schedules') }],
            ['g j', { description: 'Go to Jobs', handler: () => this.navigate('/jobs') }],
            ['g f', { description: 'Go to Freshness', handler: () => this.navigate('/freshness') }],
            ['g d', { description: 'Go to Diagnostics', handler: () => this.navigate('/diagnostics') }],
            ['g t', { description: 'Go to Tier & Usage', handler: () => this.navigate('/tier') }],
            ['g p', { description: 'Go to Setup', handler: () => this.navigate('/setup') }],
            ['Escape', { description: 'Close modal/dropdown', handler: () => this.closeActive() }],
        ]);

        // Modifier shortcuts (Cmd/Ctrl)
        this.modifierShortcuts = new Map([
            ['k', { description: 'Quick search', handler: () => this.openQuickSearch() }],
            ['s', { description: 'Save form', handler: (e) => this.saveForm(e) }],
            ['Enter', { description: 'Run sync', handler: () => this.runSync() }],
        ]);

        this.sequence = '';
        this.sequenceTimeout = null;
        this.enabled = true;

        this.init();
    }

    init() {
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
    }

    /**
     * Enable or disable keyboard shortcuts.
     * @param {boolean} enabled
     */
    setEnabled(enabled) {
        this.enabled = enabled;
    }

    /**
     * Handle keydown events.
     * @param {KeyboardEvent} e
     */
    handleKeydown(e) {
        if (!this.enabled) return;

        // Ignore when typing in inputs (unless it's Escape)
        if (e.key !== 'Escape' && this.isTypingInInput(e.target)) {
            return;
        }

        const isMod = e.metaKey || e.ctrlKey;
        const key = e.key;

        // Handle modifier shortcuts (Cmd/Ctrl + key)
        if (isMod && this.modifierShortcuts.has(key)) {
            e.preventDefault();
            this.modifierShortcuts.get(key).handler(e);
            return;
        }

        // Handle Escape specially
        if (key === 'Escape') {
            this.closeActive();
            return;
        }

        // Handle sequences (like 'g h')
        clearTimeout(this.sequenceTimeout);
        this.sequence += key + ' ';
        this.sequenceTimeout = setTimeout(() => this.sequence = '', 500);

        const seq = this.sequence.trim();

        // Check for sequence match
        if (this.shortcuts.has(seq)) {
            e.preventDefault();
            this.shortcuts.get(seq).handler();
            this.sequence = '';
            return;
        }

        // Check for single key match (only if no sequence in progress)
        if (this.sequence.trim().split(' ').length === 1 && this.shortcuts.has(key)) {
            e.preventDefault();
            this.shortcuts.get(key).handler();
            this.sequence = '';
        }
    }

    /**
     * Check if user is typing in an input field.
     * @param {HTMLElement} target
     * @returns {boolean}
     */
    isTypingInInput(target) {
        const tagName = target.tagName.toLowerCase();
        if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
            return true;
        }
        // Also check for contenteditable
        if (target.isContentEditable) {
            return true;
        }
        return false;
    }

    /**
     * Show the shortcuts help modal.
     */
    showHelp() {
        const modal = document.getElementById('shortcuts-modal');
        if (modal) {
            modal.classList.add('open');
            modal.setAttribute('aria-hidden', 'false');
            // Focus the close button for accessibility
            const closeBtn = modal.querySelector('.modal-close, button');
            if (closeBtn) closeBtn.focus();
        }
    }

    /**
     * Hide the shortcuts help modal.
     */
    hideHelp() {
        const modal = document.getElementById('shortcuts-modal');
        if (modal) {
            modal.classList.remove('open');
            modal.setAttribute('aria-hidden', 'true');
        }
    }

    /**
     * Navigate to a URL.
     * @param {string} path
     */
    navigate(path) {
        window.location.href = path;
    }

    /**
     * Focus the search input.
     */
    focusSearch() {
        const search = document.querySelector('#search-input, input[type="search"], [data-search]');
        if (search) {
            search.focus();
            search.select();
        }
    }

    /**
     * Open quick search modal (Cmd/Ctrl + K).
     */
    openQuickSearch() {
        const quickSearch = document.getElementById('quick-search');
        if (quickSearch) {
            quickSearch.classList.add('open');
            const input = quickSearch.querySelector('input');
            if (input) input.focus();
        } else {
            // Fallback to regular search focus
            this.focusSearch();
        }
    }

    /**
     * Save the current form (Cmd/Ctrl + S).
     * @param {KeyboardEvent} e
     */
    saveForm(e) {
        const form = document.querySelector('form[data-autosave], form.autosave, form');
        if (form) {
            e.preventDefault();
            const submitBtn = form.querySelector('[type="submit"], button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.click();
            }
        }
    }

    /**
     * Run sync operation (Cmd/Ctrl + Enter).
     */
    runSync() {
        const syncBtn = document.getElementById('run-sync-btn') ||
                        document.querySelector('[data-sync-button], .sync-button');
        if (syncBtn && !syncBtn.disabled) {
            syncBtn.click();
        }
    }

    /**
     * Close any active modal or dropdown.
     */
    closeActive() {
        // Close modals
        const modals = document.querySelectorAll('.modal.open, [data-modal].open');
        modals.forEach(el => {
            el.classList.remove('open');
            el.setAttribute('aria-hidden', 'true');
        });

        // Close dropdowns
        const dropdowns = document.querySelectorAll('.dropdown.open, [data-dropdown].open, .nav-dropdown.open');
        dropdowns.forEach(el => el.classList.remove('open'));

        // Close any other open panels
        const panels = document.querySelectorAll('[data-closable].open');
        panels.forEach(el => el.classList.remove('open'));

        // Blur any focused element to dismiss focus
        if (document.activeElement && document.activeElement !== document.body) {
            document.activeElement.blur();
        }
    }

    /**
     * Get all registered shortcuts for display.
     * @returns {Array<{key: string, description: string}>}
     */
    getShortcutsList() {
        const list = [];

        this.shortcuts.forEach((value, key) => {
            list.push({ key, description: value.description });
        });

        this.modifierShortcuts.forEach((value, key) => {
            const modKey = navigator.platform.includes('Mac') ? '⌘' : 'Ctrl';
            list.push({ key: `${modKey}+${key.toUpperCase()}`, description: value.description });
        });

        return list;
    }
}

// Global instance
let keyboardShortcuts;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    keyboardShortcuts = new KeyboardShortcuts();

    // Make it available globally for debugging/extension
    window.keyboardShortcuts = keyboardShortcuts;
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { KeyboardShortcuts };
}
