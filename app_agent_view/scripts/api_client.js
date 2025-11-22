
/**
 * Backend API Client for Knowledge-Weaver Chrome Extension
 * Handles communication with the FastAPI backend
 */

class BackendAPIClient {
    constructor() {
        this.baseURL = null;
        this.apiKey = null;
        this.maxRetries = 2;
        this.timeout = 60000; // 60 seconds timeout for AI operations
    }

    /**
     * Load settings from Chrome storage
     */
    async loadSettings() {
        return new Promise((resolve, reject) => {
            chrome.storage.local.get(['apiEndpoint', 'apiKey'], (result) => {
                if (chrome.runtime.lastError) {
                    reject(new Error('Failed to load settings from storage'));
                    return;
                }

                this.baseURL = result.apiEndpoint || 'http://localhost:8000';
                this.apiKey = result.apiKey || 'dev-secret-key-12345';

                console.log('API Client settings loaded:', {
                    baseURL: this.baseURL,
                    hasApiKey: !!this.apiKey
                });

                resolve();
            });
        });
    }

    /**
     * Query the knowledge base with natural language
     * @param {string} query - Natural language query
     * @param {boolean} verifiedOnly - Filter for verified content only
     * @returns {Promise<Object>} Query results
     */
    async queryKnowledgeBase(query, verifiedOnly = false) {
        if (!query || !query.trim()) {
            throw new Error('Query cannot be empty');
        }

        // Load settings if not already loaded
        if (!this.baseURL || !this.apiKey) {
            await this.loadSettings();
        }

        console.log('Querying knowledge base:', query.substring(0, 100) + '...', 'Verified Only:', verifiedOnly);

        // Retry logic with exponential backoff
        let lastError = null;

        for (let attempt = 0; attempt < this.maxRetries; attempt++) {
            try {
                const result = await this.makeRequest(query, verifiedOnly, attempt);
                return result;
            } catch (error) {
                lastError = error;
                console.warn(`Query attempt ${attempt + 1}/${this.maxRetries} failed:`, error.message);

                // If not the last attempt, wait before retrying
                if (attempt < this.maxRetries - 1) {
                    const backoffTime = Math.pow(2, attempt) * 1000; // 1s, 2s
                    console.log(`Retrying in ${backoffTime}ms...`);
                    await this.sleep(backoffTime);
                }
            }
        }

        // All retries failed
        console.error('All retry attempts failed');
        throw lastError;
    }

    /**
     * Make the actual HTTP request to the backend
     * @param {string} query - Query text
     * @param {boolean} verifiedOnly - Filter for verified content only
     * @param {number} attemptNumber - Current attempt number
     * @returns {Promise<Object>} API response
     */
    async makeRequest(query, verifiedOnly, attemptNumber) {
        const url = `${this.baseURL}/api/v1/knowledge/query`;

        console.log(`Making request (attempt ${attemptNumber + 1}):`, url);

        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.apiKey
                },
                body: JSON.stringify({
                    query: query,
                    verified_only: verifiedOnly
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // Handle HTTP errors
            if (!response.ok) {
                await this.handleHTTPError(response);
            }

            const data = await response.json();
            console.log('Query successful:', data);

            return data;

        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new Error('Request timeout (30 seconds exceeded)');
            }

            if (error.message.includes('Failed to fetch')) {
                throw new Error('Network error: Unable to reach backend API. Please check if the backend is running.');
            }

            throw error;
        }
    }

    /**
     * Handle HTTP error responses
     * @param {Response} response - Fetch response object
     */
    async handleHTTPError(response) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

        try {
            const errorData = await response.json();
            if (errorData.detail) {
                errorMessage = errorData.detail;
            }
        } catch (e) {
            // Could not parse error response
        }

        if (response.status === 401) {
            throw new Error('Authentication failed: Invalid API key');
        } else if (response.status === 400) {
            throw new Error(`Bad request: ${errorMessage}`);
        } else if (response.status === 500) {
            throw new Error('Server error: The backend encountered an error');
        } else if (response.status === 503) {
            throw new Error('Service unavailable: Backend services not initialized');
        } else {
            throw new Error(errorMessage);
        }
    }

    /**
     * Sleep utility for retry backoff
     * @param {number} ms - Milliseconds to sleep
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Analyze content for category, tags, and summary
     * @param {Object} payload - { text, url, screenshot, timestamp }
     * @returns {Promise<Object>} - Analysis result
     */
    async analyzeContent(payload) {
        // Load settings if not already loaded
        if (!this.baseURL || !this.apiKey) {
            await this.loadSettings();
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(`${this.baseURL}/api/v1/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.apiKey
                },
                body: JSON.stringify(payload),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Analysis failed: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timed out. The AI analysis is taking longer than expected.');
            }
            throw error;
        }
    }

    /**
     * Ingest knowledge manually
     * @param {Object} payload - Ingestion payload {text, screenshot, url, timestamp}
     * @returns {Promise<Object>} API response
     */
    async ingestKnowledge(payload) {
        if (!payload || !payload.text) {
            throw new Error('Payload must contain text');
        }

        // Load settings if not already loaded
        if (!this.baseURL || !this.apiKey) {
            await this.loadSettings();
        }

        const url = `${this.baseURL}/api/v1/ingest`;
        console.log('Ingesting knowledge:', url);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.apiKey
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                await this.handleHTTPError(response);
            }

            const data = await response.json();
            console.log('Ingestion successful:', data);
            return data;

        } catch (error) {
            console.error('Ingestion failed:', error);
            if (error.message.includes('Failed to fetch')) {
                throw new Error('Network error: Unable to reach backend API.');
            }
            throw error;
        }
    }

    /**
     * Test connection to backend
     * @returns {Promise<boolean>} True if connection successful
     */
    async testConnection() {
        try {
            await this.loadSettings();

            const url = `${this.baseURL}/api/v1/health`;
            const response = await fetch(url, {
                method: 'GET',
                signal: AbortSignal.timeout(3000)
            });

            if (!response.ok) {
                return false;
            }

            const data = await response.json();
            console.log('Backend health check:', data);

            return data.status === 'healthy';

        } catch (error) {
            console.error('Connection test failed:', error);
            return false;
        }
    }
}

// Export for use in content script
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BackendAPIClient };
}
