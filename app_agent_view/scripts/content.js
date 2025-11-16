/**
 * Content script for Knowledge-Weaver Chrome Extension
 * Runs on MS Teams pages to detect text selection and provide AI features
 */

console.log('Knowledge-Weaver content script loaded on Teams page');

/**
 * TextSelectionHandler - Detects text selection and shows action menu
 */
class TextSelectionHandler {
    constructor() {
        this.selectedText = '';
        this.selectionPosition = null;
        this.actionMenu = null;
        this.debounceTimer = null;

        this.init();
    }

    init() {
        // Listen for text selection
        document.addEventListener('mouseup', (e) => this.handleMouseUp(e));

        // Hide menu when clicking elsewhere
        document.addEventListener('mousedown', (e) => this.handleMouseDown(e));

        console.log('TextSelectionHandler initialized');
    }

    handleMouseUp(event) {
        // Debounce to avoid multiple triggers
        clearTimeout(this.debounceTimer);

        this.debounceTimer = setTimeout(() => {
            this.detectSelection(event);
        }, 300);
    }

    handleMouseDown(event) {
        // Hide menu if clicking outside of it
        if (this.actionMenu && !this.actionMenu.contains(event.target)) {
            this.hideActionMenu();
        }
    }

    detectSelection(event) {
        const selection = window.getSelection();
        const text = selection.toString().trim();

        // Validate text selection
        if (!this.validateTextLength(text)) {
            this.hideActionMenu();
            return;
        }

        this.selectedText = text;

        // Get selection position
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        this.selectionPosition = {
            x: rect.left + (rect.width / 2),
            y: rect.bottom + window.scrollY
        };

        // Show action menu
        this.showActionMenu(this.selectionPosition);
    }

    validateTextLength(text) {
        const length = text.length;

        if (length === 0) {
            return false;
        }

        if (length < 100) {
            console.log('Selected text too short (min 100 characters)');
            return false;
        }

        if (length > 10000) {
            console.log('Selected text too long (max 10,000 characters)');
            return false;
        }

        return true;
    }

    showActionMenu(position) {
        // Remove existing menu if present
        this.hideActionMenu();

        // Create action menu
        this.actionMenu = this.createActionMenu();

        // Position the menu
        this.actionMenu.style.left = `${position.x}px`;
        this.actionMenu.style.top = `${position.y + 10}px`;
        this.actionMenu.style.transform = 'translateX(-50%)';

        // Add to page
        document.body.appendChild(this.actionMenu);

        console.log('Action menu displayed');
    }

    createActionMenu() {
        const menu = document.createElement('div');
        menu.className = 'kw-action-menu';

        // Summarize button
        const summarizeBtn = document.createElement('button');
        summarizeBtn.className = 'kw-action-btn';
        summarizeBtn.textContent = '📝 Summarize';
        summarizeBtn.addEventListener('click', () => this.handleSummarize());

        // Rephrase button
        const rephraseBtn = document.createElement('button');
        rephraseBtn.className = 'kw-action-btn';
        rephraseBtn.textContent = '✏️ Rephrase';
        rephraseBtn.addEventListener('click', () => this.handleRephrase());

        // Query KB button
        const queryBtn = document.createElement('button');
        queryBtn.className = 'kw-action-btn';
        queryBtn.textContent = '🔍 Query KB';
        queryBtn.addEventListener('click', () => this.handleQuery());

        menu.appendChild(summarizeBtn);
        menu.appendChild(rephraseBtn);
        menu.appendChild(queryBtn);

        return menu;
    }

    hideActionMenu() {
        if (this.actionMenu && this.actionMenu.parentNode) {
            this.actionMenu.parentNode.removeChild(this.actionMenu);
            this.actionMenu = null;
        }
    }

    handleSummarize() {
        console.log('Summarize clicked - functionality will be implemented in next task');
        console.log('Selected text:', this.selectedText.substring(0, 100) + '...');
        alert('Summarize functionality coming soon!');
        this.hideActionMenu();
    }

    handleRephrase() {
        console.log('Rephrase clicked - functionality will be implemented in next task');
        console.log('Selected text:', this.selectedText.substring(0, 100) + '...');
        alert('Rephrase functionality coming soon!');
        this.hideActionMenu();
    }

    handleQuery() {
        console.log('Query KB clicked - functionality will be implemented in next task');
        console.log('Selected text:', this.selectedText.substring(0, 100) + '...');
        alert('Query KB functionality coming soon!');
        this.hideActionMenu();
    }
}

// Initialize the text selection handler
const textSelectionHandler = new TextSelectionHandler();
