/**
 * Robot Barrier Logger
 * Logs UI failures to the backend for AI-Native continuous improvement.
 */

const ROBOT_LOGGER = {
    /**
     * Log a barrier event to the backend
     * @param {string} selector - The CSS selector that failed
     * @param {string} error - The error message (e.g., "Element not found")
     */
    logBarrier: async (selector, error) => {
        try {
            const apiKey = await new Promise(resolve => {
                chrome.storage.local.get(['apiKey'], result => resolve(result.apiKey));
            });

            if (!apiKey) {
                console.warn("RobotLogger: No API key found, skipping log.");
                return;
            }

            const payload = {
                url: window.location.href,
                selector: selector,
                error: error,
                agent: "Antigravity Extension",
                timestamp: new Date().toISOString()
            };

            await fetch('http://localhost:8000/api/v1/log/barrier', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': apiKey
                },
                body: JSON.stringify(payload)
            });

            console.log(`RobotLogger: Logged barrier for ${selector}`);

        } catch (e) {
            console.error("RobotLogger: Failed to log barrier", e);
        }
    },

    /**
     * Helper to check if an element exists, logging if not
     * @param {string} selector - CSS selector to check
     * @returns {Element|null} - The element or null
     */
    findElement: (selector) => {
        const element = document.querySelector(selector);
        if (!element) {
            ROBOT_LOGGER.logBarrier(selector, "Element not found");
        }
        return element;
    }
};

// Expose globally
window.RobotLogger = ROBOT_LOGGER;
