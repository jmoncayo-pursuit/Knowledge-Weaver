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
    // Mock Chrome API for local testing (file protocol or localhost)
    if ((window.location.protocol === 'file:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && (typeof chrome === 'undefined' || !chrome.tabs)) {
        console.log('Running in Local Test Mode (Mocking Chrome API)');
        window.chrome = {
            tabs: {
                query: async () => [{ url: 'http://localhost:8000/demo-context', id: 123 }],
                captureVisibleTab: (winId, options, callback) => {
                    // Return a 1x1 pixel transparent gif
                    const mockScreenshot = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
                    if (callback) callback(mockScreenshot);
                    return Promise.resolve(mockScreenshot);
                }
            },
            storage: {
                local: {
                    get: (keys, callback) => {
                        const mockData = { apiEndpoint: 'http://localhost:8000', apiKey: 'dev-secret-key-12345' };
                        if (callback) callback(mockData);
                        return Promise.resolve(mockData);
                    },
                    set: (items, callback) => {
                        if (callback) callback();
                        return Promise.resolve();
                    }
                }
            },
            runtime: {
                lastError: null
            }
        };
    }

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

// Tab elements
const askTabBtn = document.getElementById('askTabBtn');
const contributeTabBtn = document.getElementById('contributeTabBtn');
const askTab = document.getElementById('askTab');
const contributeTab = document.getElementById('contributeTab');

// Contribute elements
const ingestInput = document.getElementById('ingestInput');
const screenshotBtn = document.getElementById('screenshotBtn');
const ingestBtn = document.getElementById('ingestBtn');
const screenshotPreview = document.getElementById('screenshotPreview');
const previewImg = document.getElementById('previewImg');
const removeScreenshotBtn = document.getElementById('removeScreenshot');

// State
let currentScreenshot = null;

// Critical element check - must happen immediately
const missingElements = [];
if (!queryInput) missingElements.push('queryInput');
if (!searchBtn) missingElements.push('searchBtn');
if (!resultsSection) missingElements.push('resultsSection');
if (!errorSection) missingElements.push('errorSection');
if (!errorMessage) missingElements.push('errorMessage');
if (!askTabBtn) missingElements.push('askTabBtn');
if (!contributeTabBtn) missingElements.push('contributeTabBtn');
if (!askTab) missingElements.push('askTab');
if (!contributeTab) missingElements.push('contributeTab');
if (!ingestInput) missingElements.push('ingestInput');
if (!screenshotBtn) missingElements.push('screenshotBtn');
if (!ingestBtn) missingElements.push('ingestBtn');
if (!screenshotPreview) missingElements.push('screenshotPreview');
if (!previewImg) missingElements.push('previewImg');
if (!removeScreenshotBtn) missingElements.push('removeScreenshot');

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

        // Tab switching logic
        askTabBtn.addEventListener('click', () => switchTab('ask'));
        contributeTabBtn.addEventListener('click', () => switchTab('contribute'));

        // Screenshot logic
        screenshotBtn.addEventListener('click', handleScreenshot);
        removeScreenshotBtn.addEventListener('click', removeScreenshot);

        // Ingest logic
        ingestBtn.addEventListener('click', handleAnalyze);

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

        // Check for verified status
        const isVerified = result.metadata && result.metadata.verification_status === 'verified_human';
        const verifiedBadge = isVerified ? '<span class="verified-badge">✅ Verified</span>' : '';

        resultItem.innerHTML = `
            <div class="result-content">${result.content}</div>
            <div class="result-meta">
                <div>
                    <small>Source: ${participants} • ${date} ${verifiedBadge}</small>
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

/**
 * Switch between Ask and Contribute tabs
 */
function switchTab(tabName) {
    if (tabName === 'ask') {
        askTab.classList.remove('hidden');
        askTab.classList.add('active');
        contributeTab.classList.add('hidden');
        contributeTab.classList.remove('active');

        askTabBtn.classList.add('active');
        contributeTabBtn.classList.remove('active');
    } else if (tabName === 'contribute') {
        contributeTab.classList.remove('hidden');
        contributeTab.classList.add('active');
        askTab.classList.add('hidden');
        askTab.classList.remove('active');

        contributeTabBtn.classList.add('active');
        askTabBtn.classList.remove('active');
    }
}

/**
 * Handle screenshot capture
 */
function handleScreenshot() {
    console.log('Capturing screenshot...');
    chrome.tabs.captureVisibleTab(null, { format: 'png' }, (dataUrl) => {
        if (chrome.runtime.lastError) {
            console.error('Screenshot failed:', chrome.runtime.lastError);
            showError('Failed to capture screenshot: ' + chrome.runtime.lastError.message);
            return;
        }

        if (!dataUrl) {
            console.error('Screenshot failed: No data URL returned');
            showError('Failed to capture screenshot: No data returned');
            return;
        }

        currentScreenshot = dataUrl;
        previewImg.src = dataUrl;
        screenshotPreview.classList.remove('hidden');
        screenshotBtn.textContent = 'Retake Screenshot';
        console.log('Screenshot captured successfully');
    });
}

/**
 * Remove screenshot
 */
function removeScreenshot() {
    currentScreenshot = null;
    previewImg.src = '';
    screenshotPreview.classList.add('hidden');
    screenshotBtn.textContent = 'Attach Screenshot';
}

/**
 * Handle ingest (Process & Save)
 */
// Review elements
const reviewSection = document.getElementById('reviewSection');
const categoryInput = document.getElementById('categoryInput');
const tagsInput = document.getElementById('tagsInput');
const summaryInput = document.getElementById('summaryInput');
const confirmBtn = document.getElementById('confirmBtn');

// State for pending ingestion
let pendingPayload = null;

if (confirmBtn) {
    confirmBtn.addEventListener('click', handleConfirm);
}

/**
 * Handle analyze content (Step 1)
 */
async function handleAnalyze() {
    const text = ingestInput.value.trim();

    if (!text && !currentScreenshot) {
        showError('Please provide text or a screenshot');
        return;
    }

    // Get current tab URL
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab ? tab.url : 'unknown';

    const payload = {
        text: text,
        screenshot: currentScreenshot,
        url: url,
        timestamp: new Date().toISOString()
    };

    console.log('Analysis Payload Ready:', payload);

    // Visual feedback
    const originalText = ingestBtn.textContent;
    ingestBtn.textContent = 'Analyzing...';
    ingestBtn.disabled = true;

    try {
        const analysis = await apiClient.analyzeContent(payload);
        console.log('Analysis Result:', analysis);

        // Populate review section
        categoryInput.value = analysis.category || '';
        tagsInput.value = (analysis.tags || []).join(', ');
        summaryInput.value = analysis.summary || '';

        // Store payload for confirmation step
        pendingPayload = payload;

        // Show review section
        reviewSection.classList.remove('hidden');
        ingestBtn.classList.add('hidden'); // Hide analyze button

        // Scroll to review section
        reviewSection.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error('Analysis error:', error);
        ingestBtn.textContent = 'Error';
        ingestBtn.classList.add('error-btn');
        ingestBtn.disabled = false;

        showError(`Failed to analyze: ${error.message}`);

        setTimeout(() => {
            ingestBtn.textContent = originalText;
            ingestBtn.classList.remove('error-btn');
        }, 3000);
    }
}

/**
 * Handle confirm and save (Step 2)
 */
async function handleConfirm() {
    if (!pendingPayload) {
        showError('No content to save');
        return;
    }

    // Update payload with reviewed data
    const finalPayload = {
        ...pendingPayload,
        category: categoryInput.value.trim(),
        tags: tagsInput.value.split(',').map(t => t.trim()).filter(t => t),
        summary: summaryInput.value.trim()
    };

    console.log('Final Ingest Payload:', finalPayload);

    // Visual feedback
    const originalText = confirmBtn.textContent;
    confirmBtn.textContent = 'Saving...';
    confirmBtn.disabled = true;

    try {
        await apiClient.ingestKnowledge(finalPayload);

        // Success feedback
        confirmBtn.textContent = 'Saved!';
        confirmBtn.classList.add('success-btn');

        // Reset form after delay
        setTimeout(() => {
            // Reset UI
            confirmBtn.textContent = originalText;
            confirmBtn.disabled = false;
            confirmBtn.classList.remove('success-btn');

            ingestInput.value = '';
            removeScreenshot();

            // Hide review section and show analyze button
            reviewSection.classList.add('hidden');
            ingestBtn.classList.remove('hidden');
            ingestBtn.textContent = 'Analyze Content';
            ingestBtn.disabled = false;

            // Clear pending payload
            pendingPayload = null;

        }, 2000);

    } catch (error) {
        console.error('Ingest error:', error);
        confirmBtn.textContent = 'Error';
        confirmBtn.classList.add('error-btn');

        showError(`Failed to save: ${error.message}`);

        setTimeout(() => {
            confirmBtn.textContent = originalText;
            confirmBtn.disabled = false;
            confirmBtn.classList.remove('error-btn');
        }, 3000);
    }
}
