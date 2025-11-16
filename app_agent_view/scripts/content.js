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
        let html = '<div style="max-height: 400px; overflow-y: auto;">';

        results.forEach((result, index) => {
            const score = (result.similarity_score * 100).toFixed(0);
            const participants = result.source.participants.join(', ');
            const date = new Date(result.source.timestamp).toLocaleDateString();

            html += `
                <div style="margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <strong>Result ${index + 1}</strong>
                        <span style="background: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                            ${score}% match
                        </span>
                    </div>
                    <div style="margin-bottom: 10px; line-height: 1.6;">
                        ${result.content}
                    </div>
                    <div style="font-size: 12px; color: #666;">
                        <div>Source: ${participants}</div>
                        <div>Date: ${date}</div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    showLoadingPopup(message) {
        this.hidePopup();

        const overlay = document.createElement('div');
        overlay.className = 'kw-overlay';
        overlay.id = 'kw-popup-overlay';

        const popup = document.createElement('div');
        popup.className = 'kw-result-popup';
        popup.innerHTML = `
            <div class="kw-result-header">
                <div class="kw-result-title">${message}</div>
            </div>
            <div class="kw-result-content" style="text-align: center; padding: 20px;">
                <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #6366f1; border-radius: 50%; animation: spin 1s linear infinite;"></div>
            </div>
        `;

        document.body.appendChild(overlay);
        document.body.appendChild(popup);
    }

    showResultPopup(title, content) {
        this.hidePopup();

        const overlay = document.createElement('div');
        overlay.className = 'kw-overlay';
        overlay.id = 'kw-popup-overlay';

        const popup = document.createElement('div');
        popup.className = 'kw-result-popup';
        popup.innerHTML = `
            <div class="kw-result-header">
                <div class="kw-result-title">${title}</div>
                <button class="kw-close-btn">×</button>
            </div>
            <div class="kw-result-content">${content}</div>
            <button class="kw-copy-btn">Copy to Clipboard</button>
        `;

        // Add event listeners
        const closeBtn = popup.querySelector('.kw-close-btn');
        closeBtn.addEventListener('click', () => this.hidePopup());

        const copyBtn = popup.querySelector('.kw-copy-btn');
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(content);
            copyBtn.textContent = '✓ Copied!';
            setTimeout(() => {
                copyBtn.textContent = 'Copy to Clipboard';
            }, 2000);
        });

        overlay.addEventListener('click', () => this.hidePopup());

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
        popup.innerHTML = `
            <div class="kw-result-header">
                <div class="kw-result-title" style="color: #d32f2f;">${title}</div>
                <button class="kw-close-btn">×</button>
            </div>
            <div class="kw-result-content" style="color: #d32f2f;">${message}</div>
            <button class="kw-copy-btn" style="background: #d32f2f;">Close</button>
        `;

        // Add event listeners
        const closeBtn = popup.querySelector('.kw-close-btn');
        closeBtn.addEventListener('click', () => this.hidePopup());

        const closeButton = popup.querySelector('.kw-copy-btn');
        closeButton.addEventListener('click', () => this.hidePopup());

        overlay.addEventListener('click', () => this.hidePopup());

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
