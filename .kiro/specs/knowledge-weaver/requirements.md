# Requirements Document

## Introduction

Knowledge-Weaver is a hybrid AI system designed to resurrect dead, unstructured knowledge from chat logs (such as MS Teams) and transform it into a living, queryable knowledge base. The system consists of three main components: a Python/FastAPI backend with RAG capabilities using Gemini API, a Chrome Extension for agents using built-in Chrome AI APIs, and a Streamlit dashboard for leadership metrics and insights.

## Glossary

- **Knowledge-Weaver System**: The complete hybrid AI application consisting of Backend API, Agent View, and Leadership View
- **Backend API**: Python/FastAPI service that analyzes chat logs, maintains Vector Database, and serves query endpoints
- **Agent View**: Chrome Extension application that provides on-device AI capabilities and queries the central Knowledge Base
- **Leadership View**: Python/Streamlit dashboard application that displays metrics and knowledge gap analysis
- **Vector Database**: RAG-based storage system containing indexed historical knowledge from chat logs
- **Knowledge Base**: The queryable repository of resurrected knowledge stored in the Vector Database
- **Agent**: Customer service or support personnel who use the Chrome Extension to access knowledge
- **Leadership User**: Manager or supervisor who uses the dashboard to monitor metrics and knowledge gaps
- **Chat Log**: Historical conversation data from platforms like MS Teams
- **Live Chat**: Real-time conversation occurring on the Teams web application
- **Gemini API**: Google's AI service used for analyzing chat logs and creating embeddings
- **Chrome AI API**: Built-in browser APIs including Summarizer API and Rewriter API
- **Summarizer API**: Chrome's on-device API for generating text summaries
- **Rewriter API**: Chrome's on-device API for rephrasing text content

## Requirements

### Requirement 1: Backend API - Chat Log Analysis

**User Story:** As a system administrator, I want the backend to analyze historical chat logs, so that critical knowledge can be extracted and indexed.

#### Acceptance Criteria

1. WHEN the Backend API receives chat log data, THE Backend API SHALL send the data to the Gemini API for analysis
2. WHEN the Gemini API returns analyzed content, THE Backend API SHALL create vector embeddings for the extracted knowledge
3. THE Backend API SHALL store the vector embeddings in the Vector Database
4. WHEN chat log analysis fails, THE Backend API SHALL log the error with timestamp and source identifier
5. THE Backend API SHALL process chat logs in batches of no more than 100 messages per request to the Gemini API

### Requirement 2: Backend API - Knowledge Query Service

**User Story:** As an agent, I want to query the central Knowledge Base, so that I can retrieve official answers to policy questions.

#### Acceptance Criteria

1. THE Backend API SHALL expose a REST endpoint that accepts natural language queries
2. WHEN the Backend API receives a query request, THE Backend API SHALL perform vector similarity search against the Vector Database
3. WHEN relevant knowledge is found with similarity score above 0.7, THE Backend API SHALL return the top 3 matching results
4. THE Backend API SHALL include source metadata with each result including original chat timestamp and participants
5. WHEN no relevant knowledge is found with similarity score above 0.7, THE Backend API SHALL return an empty result set with status indicator

### Requirement 3: Agent View - Live Chat Summarization

**User Story:** As an agent, I want to summarize highlighted live chat text, so that I can quickly understand long conversations.

#### Acceptance Criteria

1. WHEN an agent highlights text on the Teams web application, THE Agent View SHALL detect the text selection event
2. WHEN the agent triggers the summarization action, THE Agent View SHALL send the highlighted text to the Chrome Summarizer API
3. THE Agent View SHALL display the generated summary within 2 seconds of the request
4. THE Agent View SHALL limit summarization requests to text selections between 100 and 10000 characters
5. WHEN the Summarizer API fails, THE Agent View SHALL display an error message to the agent

### Requirement 4: Agent View - Text Rephrasing for Customers

**User Story:** As an agent, I want to rephrase internal notes for customer communication, so that I can maintain professional tone.

#### Acceptance Criteria

1. WHEN an agent highlights internal note text, THE Agent View SHALL detect the text selection event
2. WHEN the agent triggers the rephrase action, THE Agent View SHALL send the text to the Chrome Rewriter API with customer-friendly tone parameter
3. THE Agent View SHALL display the rephrased text within 2 seconds of the request
4. THE Agent View SHALL provide a copy-to-clipboard button for the rephrased text
5. WHEN the Rewriter API fails, THE Agent View SHALL display an error message to the agent

### Requirement 5: Agent View - Knowledge Base Query

**User Story:** As an agent, I want to ask questions to the central Knowledge Base, so that I can get official policy answers.

#### Acceptance Criteria

1. THE Agent View SHALL provide a search interface for entering natural language queries
2. WHEN an agent submits a query, THE Agent View SHALL send the query to the Backend API query endpoint
3. WHEN the Backend API returns results, THE Agent View SHALL display the results with source metadata
4. THE Agent View SHALL provide a copy-to-clipboard button for each result
5. WHEN the query request takes longer than 5 seconds, THE Agent View SHALL display a loading indicator

### Requirement 6: Leadership View - Response Time Metrics

**User Story:** As a leadership user, I want to view average leadership response time, so that I can monitor team performance.

#### Acceptance Criteria

1. THE Leadership View SHALL display the average leadership response time metric on the dashboard
2. THE Leadership View SHALL calculate response time as the duration between agent question and leadership answer in chat logs
3. THE Leadership View SHALL update the metric every 60 seconds
4. THE Leadership View SHALL display response time in hours and minutes format
5. WHEN no response time data is available, THE Leadership View SHALL display "No data available" message

### Requirement 7: Leadership View - Unanswered Questions Tracking

**User Story:** As a leadership user, I want to see a list of unanswered agent questions, so that I can identify knowledge gaps.

#### Acceptance Criteria

1. THE Leadership View SHALL display a list of agent questions that have not received responses within 24 hours
2. THE Leadership View SHALL include the question text, timestamp, and agent identifier for each unanswered question
3. THE Leadership View SHALL sort unanswered questions by age with oldest questions first
4. THE Leadership View SHALL refresh the unanswered questions list every 60 seconds
5. THE Leadership View SHALL limit the display to the 20 oldest unanswered questions

### Requirement 8: Leadership View - Trending Topics Analysis

**User Story:** As a leadership user, I want to see trending topics and knowledge gaps, so that I can prioritize knowledge base improvements.

#### Acceptance Criteria

1. THE Leadership View SHALL analyze query patterns from the Backend API logs
2. THE Leadership View SHALL display the top 10 most frequently queried topics in the past 7 days
3. THE Leadership View SHALL identify topics with high query frequency but low result quality scores
4. THE Leadership View SHALL highlight potential knowledge gaps where queries return no results above similarity threshold
5. THE Leadership View SHALL update trending topics analysis every 300 seconds

### Requirement 9: Leadership View - User Interface Design

**User Story:** As a leadership user, I want a polished dark-mode interface, so that I have a professional and visually appealing experience.

#### Acceptance Criteria

1. THE Leadership View SHALL implement a dark color scheme with primary background color #1a1a1a
2. THE Leadership View SHALL use accent colors that provide minimum contrast ratio of 4.5:1 against the dark background
3. THE Leadership View SHALL organize metrics into distinct visual sections with clear headings
4. THE Leadership View SHALL use data visualization components for metrics display including charts and graphs
5. THE Leadership View SHALL maintain consistent spacing and typography throughout the interface

### Requirement 10: System Integration - Chrome Extension and Backend Communication

**User Story:** As an agent, I want seamless integration between the Chrome Extension and backend, so that I can access knowledge without delays.

#### Acceptance Criteria

1. THE Agent View SHALL authenticate with the Backend API using API key authentication
2. WHEN the Agent View sends a request to the Backend API, THE Agent View SHALL include the API key in the request header
3. WHEN the Backend API receives an unauthenticated request, THE Backend API SHALL return HTTP 401 status code
4. THE Agent View SHALL retry failed Backend API requests up to 2 times with exponential backoff
5. WHEN all retry attempts fail, THE Agent View SHALL display an error message to the agent

### Requirement 11: Backend API - Vector Database Management

**User Story:** As a system administrator, I want the backend to maintain the Vector Database efficiently, so that queries remain fast and accurate.

#### Acceptance Criteria

1. THE Backend API SHALL initialize the Vector Database on first startup if it does not exist
2. THE Backend API SHALL support incremental updates to the Vector Database when new chat logs are processed
3. WHEN performing vector similarity search, THE Backend API SHALL return results within 1 second for 95% of queries
4. THE Backend API SHALL maintain an index of at least 10000 knowledge entries in the Vector Database
5. THE Backend API SHALL persist the Vector Database to disk every 300 seconds

### Requirement 12: Agent View - Chrome Extension Installation and Permissions

**User Story:** As an agent, I want to install the Chrome Extension easily, so that I can start using the knowledge tools quickly.

#### Acceptance Criteria

1. THE Agent View SHALL request only the minimum required Chrome permissions for text selection and API access
2. THE Agent View SHALL provide clear permission descriptions during installation
3. WHEN installed, THE Agent View SHALL display an icon in the Chrome toolbar
4. THE Agent View SHALL activate on Teams web application pages matching the pattern "teams.microsoft.com/*"
5. THE Agent View SHALL store the Backend API endpoint URL in Chrome local storage
