/**
 * Background service worker for Knowledge-Weaver Chrome Extension
 */

console.log('Knowledge-Weaver background service worker loaded');

// Listen for extension installation
chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
        console.log('Knowledge-Weaver extension installed');

        // Set default settings
        chrome.storage.local.set({
            apiEndpoint: 'http://localhost:8000',
            apiKey: 'dev-secret-key-12345'
        });
    } else if (details.reason === 'update') {
        console.log('Knowledge-Weaver extension updated');
    }
});

// Handle messages from content scripts or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Background received message:', request);

    if (request.action === 'getSettings') {
        chrome.storage.local.get(['apiEndpoint', 'apiKey'], (result) => {
            sendResponse(result);
        });
        return true; // Keep channel open for async response
    }

    if (request.action === 'saveSettings') {
        chrome.storage.local.set(request.settings, () => {
            sendResponse({ success: true });
        });
        return true;
    }
});
