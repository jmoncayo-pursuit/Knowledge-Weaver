/**
 * Chrome AI Integration for Knowledge-Weaver
 * Interfaces with Chrome's built-in AI APIs for on-device processing
 */

/**
 * SummarizerService - Uses Chrome's Summarizer API for text summarization
 */
class SummarizerService {
    constructor() {
        this.summarizer = null;
        this.isAvailable = false;
        this.checkAvailability();
    }

    async checkAvailability() {
        try {
            // Check if Chrome AI Summarizer API is available
            if ('ai' in self && 'summarizer' in self.ai) {
                const availability = await self.ai.summarizer.capabilities();
                this.isAvailable = availability.available === 'readily';

                if (this.isAvailable) {
                    console.log('Chrome Summarizer API is available');
                } else {
                    console.warn('Chrome Summarizer API not readily available:', availability.available);
                }
            } else {
                console.warn('Chrome AI Summarizer API not found');
            }
        } catch (error) {
            console.error('Error checking Summarizer API availability:', error);
        }
    }

    validateTextLength(text) {
        const length = text.length;

        if (length < 100) {
            throw new Error('Text too short for summarization (minimum 100 characters)');
        }

        if (length > 10000) {
            throw new Error('Text too long for summarization (maximum 10,000 characters)');
        }

        return true;
    }

    async summarize(text) {
        try {
            // Validate text length
            this.validateTextLength(text);

            // Check if API is available
            if (!this.isAvailable) {
                throw new Error('Chrome Summarizer API is not available. Please ensure you are using Chrome 127+ with AI features enabled.');
            }

            // Create summarizer if not already created
            if (!this.summarizer) {
                console.log('Creating summarizer instance...');
                this.summarizer = await self.ai.summarizer.create();
            }

            // Set up timeout promise (2 seconds)
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Summarization timeout (2 seconds exceeded)')), 2000);
            });

            // Summarize with timeout
            console.log('Summarizing text...');
            const summaryPromise = this.summarizer.summarize(text);

            const summary = await Promise.race([summaryPromise, timeoutPromise]);

            console.log('Summarization complete');
            return summary;

        } catch (error) {
            console.error('Summarization failed:', error);
            this.handleError(error);
            throw error;
        }
    }

    handleError(error) {
        // Log detailed error information
        if (error.message.includes('timeout')) {
            console.error('Summarization took too long');
        } else if (error.message.includes('not available')) {
            console.error('Chrome AI features not enabled');
        } else {
            console.error('Unexpected summarization error:', error);
        }
    }

    async destroy() {
        if (this.summarizer) {
            try {
                await this.summarizer.destroy();
                this.summarizer = null;
                console.log('Summarizer instance destroyed');
            } catch (error) {
                console.error('Error destroying summarizer:', error);
            }
        }
    }
}


/**
 * RewriterService - Uses Chrome's Rewriter API for text rephrasing
 */
class RewriterService {
    constructor() {
        this.rewriter = null;
        this.isAvailable = false;
        this.checkAvailability();
    }

    async checkAvailability() {
        try {
            // Check if Chrome AI Rewriter API is available
            if ('ai' in self && 'rewriter' in self.ai) {
                const availability = await self.ai.rewriter.capabilities();
                this.isAvailable = availability.available === 'readily';

                if (this.isAvailable) {
                    console.log('Chrome Rewriter API is available');
                } else {
                    console.warn('Chrome Rewriter API not readily available:', availability.available);
                }
            } else {
                console.warn('Chrome AI Rewriter API not found');
            }
        } catch (error) {
            console.error('Error checking Rewriter API availability:', error);
        }
    }

    validateTextLength(text) {
        const length = text.length;

        if (length < 100) {
            throw new Error('Text too short for rephrasing (minimum 100 characters)');
        }

        if (length > 10000) {
            throw new Error('Text too long for rephrasing (maximum 10,000 characters)');
        }

        return true;
    }

    async rephrase(text, tone = 'more-formal') {
        try {
            // Validate text length
            this.validateTextLength(text);

            // Check if API is available
            if (!this.isAvailable) {
                throw new Error('Chrome Rewriter API is not available. Please ensure you are using Chrome 127+ with AI features enabled.');
            }

            // Create rewriter if not already created
            if (!this.rewriter) {
                console.log('Creating rewriter instance with tone:', tone);
                this.rewriter = await self.ai.rewriter.create({
                    tone: tone,
                    length: 'as-is'
                });
            }

            // Set up timeout promise (2 seconds)
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Rephrasing timeout (2 seconds exceeded)')), 2000);
            });

            // Rephrase with timeout
            console.log('Rephrasing text...');
            const rephrasePromise = this.rewriter.rewrite(text);

            const rephrased = await Promise.race([rephrasePromise, timeoutPromise]);

            console.log('Rephrasing complete');
            return rephrased;

        } catch (error) {
            console.error('Rephrasing failed:', error);
            this.handleError(error);
            throw error;
        }
    }

    handleError(error) {
        // Log detailed error information
        if (error.message.includes('timeout')) {
            console.error('Rephrasing took too long');
        } else if (error.message.includes('not available')) {
            console.error('Chrome AI features not enabled');
        } else {
            console.error('Unexpected rephrasing error:', error);
        }
    }

    async destroy() {
        if (this.rewriter) {
            try {
                await this.rewriter.destroy();
                this.rewriter = null;
                console.log('Rewriter instance destroyed');
            } catch (error) {
                console.error('Error destroying rewriter:', error);
            }
        }
    }
}

// Export for use in content script
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SummarizerService, RewriterService };
}
