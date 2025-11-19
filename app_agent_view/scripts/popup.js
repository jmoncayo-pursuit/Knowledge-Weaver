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

    // Debug: Check if all elements are found
    console.log('DOM Elements Check:');
    console.log('queryInput:', queryInput);
    console.log('searchBtn:', searchBtn);
    console.log('loadingIndicator:', loadingIndicator);
    console.log('resultsSection:', resultsSection);
    console.log('resultsList:', resultsList);
    console.log('errorSection:', errorSection);

    // Verify critical elements exist
    if (!queryInput || !searchBtn) {
        console.error('CRITICAL: Search elements not found!');
        return;
    }

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

    retryBtn.addEventListener('click', handleSearch);
    settingsLink.addEventListener('click', openSettings);
    closeSettings.addEventListener('click', closeSettingsModal);
    saveSettingsBtn.addEventListener('click', saveSettings);

    // Allow Enter key to submit query
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            console.log('Enter key pressed, triggering search...');
            handleSearch();
        }
    });

    console.log('All event listeners attached successfully');
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
