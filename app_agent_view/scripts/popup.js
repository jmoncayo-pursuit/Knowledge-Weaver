/**
 * Popup script for Knowledge-Weaver Chrome Extension
 */

console.log('Knowledge-Weaver popup loaded');

/**
 * Critical UI Error Handler - Shows errors directly in the popup
 */
function showCriticalError(message) {
    document.body.innerHTML = `
        <div style="padding: 20px; background: #ffebee; border: 2px solid #c62828; border-radius: 8px; margin: 20px;">
            <h2 style="color: #c62828; margin: 0 0 10px 0;">⚠️ Critical Error</h2>
            <p style="color: #333; margin: 0; white-space: pre-wrap; font-family: monospace;">${message}</p>
        </div>
    `;
}

// Initialize API client with error handling
let apiClient;
try {
    apiClient = new BackendAPIClient();
} catch (error) {
    showCriticalError(`Failed to initialize API client:\n${error.message}\n\nStack: ${error.stack}`);
    throw error;
}

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

// Critical element check - must happen immediately
const missingElements = [];
if (!queryInput) missingElements.push('queryInput');
if (!searchBtn) missingElements.push('searchBtn');
if (!resultsSection) missingElements.push('resultsSection');
if (!errorSection) missingElements.push('errorSection');
if (!errorMessage) missingElements.push('errorMessage');

if (missingElements.length > 0) {
    showCriticalError(`Missing DOM elements:\n${missingElements.join('\n')}\n\nThe HTML structure may have changed.`);
    throw new Error('Critical DOM elements missing');
}

// Settings modal elements
const settingsModal = document.getElementById('settingsModal');
const closeSettings = document.getElementById('closeSettings');
const apiEndpointInput = document.getElementById('apiEndpoint');
const apiKeyInput = document.getElementById('apiKey');
const saveSettingsBtn = document.getElementById('saveSettings');
const settingsMessage = document.getElementById('settingsMessage');

// Quick test queries based on sample data
const QUERIES = [
    'missed life event deadline',
    'domestic partner verification',
    'gym reimbursement',
    'adult orthodontia',
    'FSA vs HSA conflict'
];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Popup initialized');

    try {
        // Load saved settings
        loadSettings();

        // Initialize quick test chips
        initializeQuickTestChips();

        // Event listeners
        console.log('Attaching search button click listener...');
        searchBtn.addEventListener('click', () => {
            console.log('Search button clicked!');
            handleSearch();
        });

        if (retryBtn) {
            retryBtn.addEventListener('click', handleSearch);
        }

        if (settingsLink) {
            settingsLink.addEventListener('click', openSettings);
        }

        if (closeSettings) {
            closeSettings.addEventListener('click', closeSettingsModal);
        }

        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', saveSettings);
        }

        // Allow Enter key to submit query
        queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log('Enter key pressed, triggering search...');
                handleSearch();
            }
        });

        console.log('All event listeners attached successfully');
    } catch (error) {
        showCriticalError(`Initialization failed:\n${error.message}\n\nStack: ${error.stack}`);
    }
});

/**
 * Initialize quick test chips for easy testing
 */
function initializeQuickTestChips() {
    const chipsContainer = document.getElementById('quick-test-chips');

    QUERIES.forEach(query => {
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.textContent = query;
        chip.addEventListener('click', () => {
            queryInput.value = query;
            handleSearch();
        });
        chipsContainer.appendChild(chip);
    });

    console.log('Quick test chips initialized');
}

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
    console.log('handleSearch() called');

    try {
        const query = queryInput.value.trim();
        console.log('Query value:', query);

        if (!query) {
            console.log('Empty query, showing error');
            showError('Please enter a question');
            return;
        }

        // Hide all sections
        hideAllSections();

        // Show loading
        loadingIndicator.classList.remove('hidden');
        console.log('Loading indicator shown');

        try {
            console.log('Querying knowledge base:', query);

            // Query the knowledge base
            const result = await apiClient.queryKnowledgeBase(query);
            console.log('Query result:', result);

            // Hide loading
            loadingIndicator.classList.add('hidden');

            // Display results
            if (result.results && result.results.length > 0) {
                console.log('Displaying', result.results.length, 'results');
                displayResults(result.results);
            } else {
                console.log('No results found');
                showError('No relevant knowledge found for your query');
            }

        } catch (error) {
            console.error('Query error:', error);
            loadingIndicator.classList.add('hidden');

            // Show detailed error message
            const errorDetails = `
Error: ${error.message}

Type: ${error.name}

Stack: ${error.stack || 'No stack trace available'}

API Client Status: ${apiClient ? 'Initialized' : 'Not initialized'}
            `.trim();

            showError(errorDetails);
        }
    } catch (outerError) {
        // Catch any errors in the outer try block
        console.error('Critical error in handleSearch:', outerError);
        showCriticalError(`Search function failed:\n${outerError.message}\n\nStack: ${outerError.stack}`);
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
    try {
        hideAllSections();
        if (errorMessage && errorSection) {
            errorMessage.textContent = message;
            errorSection.classList.remove('hidden');
        } else {
            // Fallback if error elements don't exist
            showCriticalError(`Error display failed. Original error:\n${message}`);
        }
    } catch (error) {
        showCriticalError(`Failed to show error:\n${error.message}\n\nOriginal error:\n${message}`);
    }
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
