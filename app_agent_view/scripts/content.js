/**
 * Content script for Knowledge-Weaver Chrome Extension
 * Runs on MS Teams pages to detect text selection and provide AI features
 */

console.log('Knowledge-Weaver content script loaded on Teams page');

// Initialize Chrome AI services
const summarizerService = new SummarizerService();
const rewriterService = new RewriterService();

// Initialize Backend API client
const apiClient = new BackendAPIClient();

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

    async handleSummarize() {
        console.log('Summarize clicked');
        console.log('Selected text:', this.selectedText.substring(0, 100) + '...');

        this.hideActionMenu();

        try {
            // Show loading indicator
            this.showLoadingPopup('Summarizing...');

            // Call summarizer service
            const summary = await summarizerService.summarize(this.selectedText);

            // Show result
            this.showResultPopup('Summary', summary);

        } catch (error) {
            console.error('Summarization error:', error);
            this.showErrorPopup('Summarization Failed', error.message);
        }
    }

    async handleRephrase() {
        console.log('Rephrase clicked');
        console.log('Selected text:', this.selectedText.substring(0, 100) + '...');

        this.hideActionMenu();

        try {
            // Show loading indicator
            this.showLoadingPopup('Rephrasing for customer...');

            // Call rewriter service with customer-friendly tone
            const rephrased = await rewriterService.rephrase(this.selectedText, 'more-formal');

            // Show result
            this.showResultPopup('Rephrased Text', rephrased);

        } catch (error) {
            console.error('Rephrasing error:', error);
            this.showErrorPopup('Rephrasing Failed', error.message);
        }
    }

    async handleQuery() {
        console.log('Query KB clicked');
        console.log('Selected text:', this.selectedText.substring(0, 100) + '...');

        this.hideActionMenu();

        try {
            // Show loading indicator
            this.showLoadingPopup('Querying Knowledge Base...');

            // Call backend API to query knowledge base
            const result = await apiClient.queryKnowledgeBase(this.selectedText);

            // Format and display results
            if (result.results && result.results.length > 0) {
                const formattedResults = this.formatQueryResults(result.results);
                this.showResultPopup('Knowledge Base Results', formattedResults);
            } else {
                this.showErrorPopup('No Results Found', 'No relevant knowledge found in the database for your query.');
            }

        } catch (error) {
            console.error('Query error:', error);
            this.showErrorPopup('Query Failed', error.message);
        }
    }

    formatQueryResults(results) {
        // Format results as plain text instead of HTML
        let text = '';

        results.forEach((result, index) => {
            const score = (result.similarity_score * 100).toFixed(0);
            const participants = result.source.participants.join(', ');
            const date = new Date(result.source.timestamp).toLocaleDateString();

            text += `Result ${index + 1} (${score}% match)\n\n`;
            text += `${result.content}\n\n`;
            text += `Source: ${participants}\n`;
            text += `Date: ${date}\n`;

            if (index < results.length - 1) {
                text += '\n---\n\n';
            }
        });

        return text;
    }

    showLoadingPopup(message) {
        this.hidePopup();

        const overlay = document.createElement('div');
        overlay.className = 'kw-overlay';
        overlay.id = 'kw-popup-overlay';

        const popup = document.createElement('div');
        popup.className = 'kw-result-popup';

        // Create header
        const header = document.createElement('div');
        header.className = 'kw-result-header';

        const title = document.createElement('div');
        title.className = 'kw-result-title';
        title.textContent = message;

        header.appendChild(title);

        // Create content with spinner
        const content = document.createElement('div');
        content.className = 'kw-result-content';
        content.style.textAlign = 'center';
        content.style.padding = '20px';

        const spinner = document.createElement('div');
        spinner.className = 'kw-spinner';

        content.appendChild(spinner);

        popup.appendChild(header);
        popup.appendChild(content);

        document.body.appendChild(overlay);
        document.body.appendChild(popup);
    }

    showResultPopup(title, contentText) {
        this.hidePopup();

        const overlay = document.createElement('div');
        overlay.className = 'kw-overlay';
        overlay.id = 'kw-popup-overlay';

        const popup = document.createElement('div');
        popup.className = 'kw-result-popup';

        // Create header
        const header = document.createElement('div');
        header.className = 'kw-result-header';

        const titleDiv = document.createElement('div');
        titleDiv.className = 'kw-result-title';
        titleDiv.textContent = title;

        const closeBtn = document.createElement('button');
        closeBtn.className = 'kw-close-btn';
        closeBtn.textContent = '×';
        closeBtn.addEventListener('click', () => this.hidePopup());

        header.appendChild(titleDiv);
        header.appendChild(closeBtn);

        // Create content - use textContent to avoid TrustedHTML issues
        const content = document.createElement('div');
        content.className = 'kw-result-content';
        content.textContent = contentText;

        // Create copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'kw-copy-btn';
        copyBtn.textContent = 'Copy to Clipboard';
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(contentText).then(() => {
                copyBtn.textContent = '✓ Copied!';
                setTimeout(() => {
                    copyBtn.textContent = 'Copy to Clipboard';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
            });
        });

        overlay.addEventListener('click', () => this.hidePopup());

        popup.appendChild(header);
        popup.appendChild(content);
        popup.appendChild(copyBtn);

        document.body.appendChild(overlay);
        document.body.appendChild(popup);
    }

    showErrorPopup(title, message) {
        this.hidePopup();

        const overlay = document.createElement('div');
        overlay.className = 'kw-overlay';
        overlay.id = 'kw-popup-overlay';

        const popup = document.createElement('div');
        popup.className = 'kw-result-popup';

        // Create header
        const header = document.createElement('div');
        header.className = 'kw-result-header';

        const titleDiv = document.createElement('div');
        titleDiv.className = 'kw-result-title';
        titleDiv.style.color = '#d32f2f';
        titleDiv.textContent = title;

        const closeBtn = document.createElement('button');
        closeBtn.className = 'kw-close-btn';
        closeBtn.textContent = '×';
        closeBtn.addEventListener('click', () => this.hidePopup());

        header.appendChild(titleDiv);
        header.appendChild(closeBtn);

        // Create content - use textContent to avoid TrustedHTML issues
        const content = document.createElement('div');
        content.className = 'kw-result-content';
        content.style.color = '#d32f2f';
        content.textContent = message;

        // Create close button
        const closeButton = document.createElement('button');
        closeButton.className = 'kw-copy-btn';
        closeButton.style.background = '#d32f2f';
        closeButton.textContent = 'Close';
        closeButton.addEventListener('click', () => this.hidePopup());

        overlay.addEventListener('click', () => this.hidePopup());

        popup.appendChild(header);
        popup.appendChild(content);
        popup.appendChild(closeButton);

        document.body.appendChild(overlay);
        document.body.appendChild(popup);
    }

    hidePopup() {
        const overlay = document.getElementById('kw-popup-overlay');
        if (overlay) {
            overlay.remove();
        }

        const popups = document.querySelectorAll('.kw-result-popup');
        popups.forEach(popup => popup.remove());
    }
}

// Initialize the text selection handler
const textSelectionHandler = new TextSelectionHandler();
