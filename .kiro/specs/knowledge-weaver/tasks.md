# Implementation Plan

## Backend API Implementation

- [x] 1. Set up Backend API project structure and dependencies
  - Create directory structure for models, services, and API routes
  - Create requirements.txt with FastAPI, ChromaDB, google-generativeai, python-dotenv, uvicorn
  - Create main.py entry point with FastAPI app initialization
  - Set up environment variable loading from .env file
  - _Requirements: 11.1_

- [x] 2. Implement data models and schemas
  - [x] 2.1 Create Pydantic models for ChatMessage, KnowledgeEntry, QueryResult
    - Write ChatMessage model with id, timestamp, sender, content, platform fields
    - Write KnowledgeEntry model with id, content, entry_type, source_messages, timestamp, participants
    - Write QueryResult and KnowledgeMatch models for API responses
    - Write SourceMetadata model for result metadata
    - _Requirements: 1.1, 2.4_
  - [x] 2.2 Create request/response schemas for API endpoints
    - Write ProcessChatLogsRequest schema
    - Write QueryRequest schema with query field
    - Write ProcessingResult and error response schemas
    - _Requirements: 1.1, 2.1_

- [x] 3. Implement Vector Database Manager
  - [x] 3.1 Create VectorDatabase class with ChromaDB integration
    - Write __init__ method to initialize ChromaDB client with persist directory
    - Implement initialize() method to create collection if not exists
    - Implement add_knowledge() method to store embeddings with metadata
    - Implement search() method with similarity threshold filtering
    - Implement persist() method for disk persistence
    - _Requirements: 11.1, 11.2, 11.3, 11.5_
  - [x] 3.2 Add database initialization on application startup
    - Create startup event handler in main.py
    - Initialize VectorDatabase instance
    - Verify collection exists or create it
    - _Requirements: 11.1_

- [x] 4. Implement Gemini API client
  - [x] 4.1 Create GeminiClient class for API interactions
    - Write __init__ method to configure Gemini API with key from environment
    - Implement extract_knowledge() method to analyze chat messages
    - Implement generate_embedding() method for text embeddings
    - Add error handling with retry logic for transient failures
    - _Requirements: 1.1, 1.2, 1.4_
  - [x] 4.2 Add batch processing logic for chat messages
    - Implement batch splitting to max 100 messages per request
    - Add validation for batch size limits
    - _Requirements: 1.5_

- [x] 5. Implement Chat Log Processor service
  - [x] 5.1 Create ChatLogProcessor class
    - Write __init__ method accepting GeminiClient and VectorDatabase dependencies
    - Implement process_chat_logs() method for end-to-end processing
    - Implement extract_knowledge() to parse Gemini responses into KnowledgeEntry objects
    - Implement create_embeddings() to generate vectors for knowledge entries
    - Add error logging with timestamp and source identifier
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 6. Implement Query Service
  - [x] 6.1 Create QueryService class
    - Write __init__ method accepting VectorDatabase and GeminiClient dependencies
    - Implement query_knowledge_base() method for natural language queries
    - Implement generate_query_embedding() to create query vectors
    - Implement search_similar_knowledge() with 0.7 similarity threshold
    - Return top 3 matches with source metadata
    - Handle empty result sets when no matches above threshold
    - Add query logging for analytics
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 7. Implement API authentication middleware
  - [x] 7.1 Create API key authentication
    - Write authentication dependency function to validate API key header
    - Return 401 for missing or invalid API keys
    - Add API key configuration in environment variables
    - _Requirements: 10.3_

- [x] 8. Implement API endpoints
  - [x] 8.1 Create /api/v1/chat-logs/process endpoint
    - Write POST endpoint handler
    - Add authentication dependency
    - Validate request body with Pydantic schema
    - Call ChatLogProcessor.process_chat_logs()
    - Return ProcessingResult with success count and errors
    - _Requirements: 1.1, 1.2, 1.3_
  - [x] 8.2 Create /api/v1/knowledge/query endpoint
    - Write POST endpoint handler
    - Add authentication dependency
    - Validate request body with query field
    - Call QueryService.query_knowledge_base()
    - Return QueryResult with matches and metadata
    - Add 5-second timeout handling
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - [x] 8.3 Create /api/v1/metrics/queries endpoint
    - Write GET endpoint handler
    - Add authentication dependency
    - Accept start_date, end_date, limit query parameters
    - Return query log entries from storage
    - _Requirements: 8.1_
  - [x] 8.4 Create /api/v1/metrics/unanswered endpoint
    - Write GET endpoint handler
    - Add authentication dependency
    - Return unanswered questions from chat log analysis
    - _Requirements: 7.1, 7.2_
  - [x] 8.5 Create /api/v1/health endpoint
    - Write GET endpoint handler (no authentication)
    - Check Vector Database connectivity
    - Return health status JSON
    - _Requirements: 11.1_

- [ ] 9. Add CORS configuration and error handling
  - [ ] 9.1 Configure CORS middleware
    - Add CORS middleware to FastAPI app
    - Configure allowed origins for Chrome Extension and Streamlit
    - _Requirements: 10.1_
  - [ ] 9.2 Add global exception handlers
    - Create exception handler for Gemini API errors (return 503)
    - Create exception handler for Vector DB errors (return 500)
    - Create exception handler for validation errors (return 422)
    - Add structured error logging
    - _Requirements: 1.4_

- [ ] 10. Add background task for Vector Database persistence
  - [ ] 10.1 Implement periodic persistence task
    - Create background task to persist Vector DB every 300 seconds
    - Add task scheduler using asyncio
    - Start task on application startup
    - _Requirements: 11.5_

## Chrome Extension (Agent View) Implementation

- [ ] 11. Set up Chrome Extension project structure
  - Create manifest.json with Manifest V3 configuration
  - Define required permissions (activeTab, storage, scripting)
  - Configure content scripts for teams.microsoft.com/*
  - Create directory structure for scripts, popup, and styles
  - _Requirements: 12.1, 12.3, 12.4_

- [ ] 12. Implement content script for text selection
  - [ ] 12.1 Create TextSelectionHandler class
    - Write selection detection logic using mouseup event
    - Implement text validation (100-10,000 characters)
    - Add position calculation for action menu
    - _Requirements: 3.1, 4.1_
  - [ ] 12.2 Create ActionMenu component
    - Write menu rendering logic with Summarize, Rephrase, Query buttons
    - Implement positioning near text selection
    - Add click handlers for each action
    - Add menu hide/show logic
    - _Requirements: 3.2, 4.2, 5.2_

- [ ] 13. Implement Chrome AI integration
  - [ ] 13.1 Create SummarizerService class
    - Write summarize() method using chrome.ai.summarizer API
    - Add text length validation (100-10,000 chars)
    - Implement 2-second timeout handling
    - Add error handling with user-friendly messages
    - _Requirements: 3.2, 3.3, 3.4, 3.5_
  - [ ] 13.2 Create RewriterService class
    - Write rephrase() method using chrome.ai.rewriter API
    - Configure customer-friendly tone parameter
    - Add text length validation
    - Implement 2-second timeout handling
    - Add copy-to-clipboard functionality
    - Add error handling with user-friendly messages
    - _Requirements: 4.2, 4.3, 4.4, 4.5_

- [ ] 14. Implement Backend API client for Extension
  - [ ] 14.1 Create BackendAPIClient class
    - Write constructor accepting baseURL and apiKey
    - Implement queryKnowledgeBase() method
    - Add API key authentication in request headers
    - Implement exponential backoff retry (2 attempts)
    - Add 5-second loading indicator logic
    - Add error handling for auth and network errors
    - _Requirements: 5.2, 5.5, 10.1, 10.2, 10.4, 10.5_

- [ ] 15. Implement Extension popup UI
  - [ ] 15.1 Create popup HTML and CSS
    - Design search interface with input field and submit button
    - Create results display area with copy buttons
    - Add settings panel for API endpoint configuration
    - Style with modern, clean design
    - _Requirements: 5.1, 5.4_
  - [ ] 15.2 Create popup JavaScript logic
    - Implement query submission handler
    - Add loading state management
    - Implement results rendering with source metadata
    - Add copy-to-clipboard for each result
    - Load API endpoint from Chrome storage
    - Add error display with retry option
    - _Requirements: 5.2, 5.3, 5.4, 12.5_

- [ ] 16. Add Extension configuration and storage
  - [ ] 16.1 Implement settings management
    - Create settings page for API endpoint URL configuration
    - Store settings in Chrome local storage
    - Load settings on extension initialization
    - _Requirements: 12.5_

## Streamlit Dashboard (Leadership View) Implementation

- [ ] 17. Set up Streamlit project structure
  - Create requirements.txt with streamlit, plotly, altair, pandas, requests
  - Create main dashboard.py file
  - Create custom CSS file for dark mode theme
  - Set up directory structure for components and utilities
  - _Requirements: 9.1_

- [ ] 18. Implement dark mode theme and styling
  - [ ] 18.1 Create custom CSS theme
    - Define CSS variables for dark color scheme (#1a1a1a background)
    - Set accent colors with 4.5:1 contrast ratio
    - Create metric card styles with borders and spacing
    - Apply consistent typography and 8px grid spacing
    - _Requirements: 9.1, 9.2, 9.3, 9.5_
  - [ ] 18.2 Apply theme to Streamlit app
    - Load custom CSS in dashboard.py
    - Configure Streamlit theme settings
    - _Requirements: 9.1_

- [ ] 19. Implement Backend API client for Dashboard
  - [ ] 19.1 Create API client utility
    - Write functions to fetch metrics from Backend API
    - Implement fetch_query_logs() for trending analysis
    - Implement fetch_unanswered_questions() for question tracking
    - Add error handling for failed requests
    - Add API key authentication
    - _Requirements: 6.1, 7.1, 8.1_

- [ ] 20. Implement metrics dashboard components
  - [ ] 20.1 Create response time metric component
    - Fetch response time data from Backend API
    - Calculate average leadership response time
    - Display in hours:minutes format
    - Handle "No data available" case
    - Add 60-second auto-refresh
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [ ] 20.2 Create query volume metric component
    - Fetch query logs for last 7 days
    - Calculate total query count
    - Display with visualization
    - _Requirements: 8.2_
  - [ ] 20.3 Create knowledge gap metric component
    - Identify queries with no results above threshold
    - Count knowledge gaps
    - Display with highlighting
    - _Requirements: 8.4_

- [ ] 21. Implement unanswered questions tracker
  - [ ] 21.1 Create unanswered questions component
    - Fetch unanswered questions from Backend API
    - Filter questions older than 24 hours
    - Sort by age (oldest first)
    - Display top 20 in table format
    - Show question text, agent, age, timestamp
    - Add 60-second auto-refresh
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 22. Implement trending topics analyzer
  - [ ] 22.1 Create trending topics component
    - Fetch query logs from Backend API
    - Extract topics using keyword extraction
    - Count topic frequency
    - Display top 10 topics in bar chart
    - Identify knowledge gaps (high frequency, low quality)
    - Highlight gaps in red where avg score < 0.5
    - Add 300-second auto-refresh
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 23. Implement main dashboard layout
  - [ ] 23.1 Create dashboard layout
    - Add dashboard title
    - Create 3-column layout for metrics
    - Add unanswered questions section
    - Add trending topics section
    - Apply visual hierarchy with section headings
    - _Requirements: 9.3, 9.4_

## Integration and Documentation

- [ ] 24. Create sample data and testing utilities
  - Create sample chat log data for testing Backend API
  - Create test scripts to populate Vector Database
  - Add example API requests for testing endpoints
  - _Requirements: 1.1, 2.1_

- [ ] 25. Create deployment configuration
  - [ ] 25.1 Create Docker configuration for Backend API
    - Write Dockerfile for Python backend
    - Create docker-compose.yml with volume mounts
    - Configure environment variables
    - _Requirements: 11.1_
  - [ ] 25.2 Create Docker configuration for Leadership View
    - Write Dockerfile for Streamlit app
    - Configure port 8501 exposure
    - _Requirements: 9.1_

- [ ] 26. Create README documentation
  - Write setup instructions for Backend API
  - Write installation guide for Chrome Extension
  - Write deployment guide for Leadership View
  - Document API endpoints and authentication
  - Add troubleshooting section
  - _Requirements: 12.2_
