/**
 * Popup script for Knowledge-Weaver Chrome Extension
 */

console.log('Knowledge-Weaver popup loaded');

// Initialize API client
const apiClient = new BackendAPIClient();

// DOM elements
const queryInput = document.getElementById('queryInput');
const searchBtn = document.getElementById('searchBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultsSection = document.getElementById('resultsSection');
const resultsList = document.getElementById('resultsList');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');
const emptyState = document.getElementById('emptyState');
const settingsLink = document.getElementById('settingsLink');

// Settings modal elements
const settingsModal = document.getElementById('settingsModal');
const closeSettings = document.getElementById('closeSettings');
const apiEndpointInput = document.getElementById('apiEndpoint');
const apiKeyInput = document.getElementById('apiKey');
const saveSettingsBtn = document.getElementById('saveSettings');
const settingsMessage = document.getElementById('settingsMessage');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Popup initialized');

    // Load saved settings
    loadSettings();

    // Event listeners
    searchBtn.addEventListener('click', handleSearch);
    retryBtn.addEventListener('click', handleSearch);
    settingsLink.addEventListener('click', openSettings);
    closeSettings.addEventListener('click', closeSettingsModal);
    saveSettingsBtn.addEventListener('click', saveSettings);

    // Allow Enter key to submit query
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSearch();
        }
    });
});

/**
 * Load settings from Chrome storage
 */
function loadSettings() {
    chrome.storage.local.get(['apiEndpoint', 'apiKey'], (result) => {
        if (result.apiEndpoint) {
            apiEndpointInput.value = result.apiEndpoint;
        }
        if (result.apiKey) {
            apiKeyInput.value = result.apiKey;
        }
        console.log('Settings loaded');
    });
}

/**
 * Open settings modal
 */
function openSettings(e) {
    e.preventDefault();
    settingsModal.classList.remove('hidden');
    settingsMessage.classList.add('hidden');
}

/**
 * Close settings modal
 */
function closeSettingsModal() {
    settingsModal.classList.add('hidden');
}

/**
 * Save settings to Chrome storage
 */
function saveSettings() {
    const apiEndpoint = apiEndpointInput.value.trim();
    const apiKey = apiKeyInput.value.trim();

    if (!apiEndpoint || !apiKey) {
        showSettingsMessage('Please fill in all fields', 'error');
        return;
    }

    chrome.storage.local.set({ apiEndpoint, apiKey }, () => {
        console.log('Settings saved');
        showSettingsMessage('Settings saved successfully!', 'success');

        // Reload API client settings
        apiClient.loadSettings();

        // Close modal after 1.5 seconds
        setTimeout(() => {
            closeSettingsModal();
        }, 1500);
    });
}

/**
 * Show settings message
 */
function showSettingsMessage(message, type) {
    settingsMessage.textContent = message;
    settingsMessage.className = `settings-message ${type}`;
    settingsMessage.classList.remove('hidden');
}

/**
 * Handle search button click
 */
async function handleSearch() {
    const query = queryInput.value.trim();

    if (!query) {
        showError('Please enter a question');
        return;
    }

    // Hide all sections
    hideAllSections();

    // Show loading
    loadingIndicator.classList.remove('hidden');

    try {
        console.log('Querying knowledge base:', query);

        // Query the knowledge base
        const result = await apiClient.queryKnowledgeBase(query);

        // Hide loading
        loadingIndicator.classList.add('hidden');

        // Display results
        if (result.results && result.results.length > 0) {
            displayResults(result.results);
        } else {
            showError('No relevant knowledge found for your query');
        }

    } catch (error) {
        console.error('Query error:', error);
        loadingIndicator.classList.add('hidden');
        showError(error.message);
    }
}

/**
 * Display query results
 */
function displayResults(results) {
    hideAllSections();

    resultsList.innerHTML = '';

    results.forEach((result, index) => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item';

        const score = (result.similarity_score * 100).toFixed(0);
        const participants = result.source.participants.join(', ');
        const date = new Date(result.source.timestamp).toLocaleDateString();

        resultItem.innerHTML = `
            <div class="result-content">${result.content}</div>
            <div class="result-meta">
                <div>
                    <small>Source: ${participants} • ${date}</small>
                </div>
                <div>
                    <span class="similarity-score">${score}%</span>
                    <button class="copy-btn" data-content="${escapeHtml(result.content)}">Copy</button>
                </div>
            </div>
        `;

        resultsList.appendChild(resultItem);
    });

    // Add copy button listeners
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const content = e.target.getAttribute('data-content');
            copyToClipboard(content, e.target);
        });
    });

    resultsSection.classList.remove('hidden');
}

/**
 * Show error message
 */
function showError(message) {
    hideAllSections();
    errorMessage.textContent = message;
    errorSection.classList.remove('hidden');
}

/**
 * Hide all sections
 */
function hideAllSections() {
    loadingIndicator.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    emptyState.classList.add('hidden');
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = '✓ Copied!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
