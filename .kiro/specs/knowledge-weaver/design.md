# Knowledge-Weaver Design Document

## Overview

Knowledge-Weaver is a hybrid AI system that resurrects dead knowledge from unstructured chat logs and transforms it into a living, queryable knowledge base. The system architecture follows a three-tier design with a centralized Python backend, a Chrome Extension for agent-facing features, and a Streamlit dashboard for leadership insights.

The system leverages both cloud-based AI (Gemini API) for heavy processing and on-device AI (Chrome AI APIs) for fast, local operations, creating a "Frankenstein" architecture that stitches together multiple AI technologies.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Knowledge-Weaver System                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │   Agent View     │         │ Leadership View  │          │
│  │ (Chrome Ext)     │         │  (Streamlit)     │          │
│  │                  │         │                  │          │
│  │ - Summarizer API │         │ - Metrics        │          │
│  │ - Rewriter API   │         │ - Analytics      │          │
│  │ - Query UI       │         │ - Dark Mode UI   │          │
│  └────────┬─────────┘         └────────┬─────────┘          │
│           │                            │                     │
│           │         REST API           │                     │
│           └────────────┬───────────────┘                     │
│                        │                                     │
│              ┌─────────▼─────────┐                          │
│              │   Backend API     │                          │
│              │  (FastAPI)        │                          │
│              │                   │                          │
│              │ - Chat Analysis   │                          │
│              │ - Query Service   │                          │
│              │ - Vector DB Mgmt  │                          │
│              └─────────┬─────────┘                          │
│                        │                                     │
│              ┌─────────▼─────────┐                          │
│              │  Vector Database  │                          │
│              │   (ChromaDB)      │                          │
│              └───────────────────┘                          │
│                        │                                     │
│              ┌─────────▼─────────┐                          │
│              │   Gemini API      │                          │
│              │  (External)       │                          │
│              └───────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend API (`/backend_api`)**
- Framework: FastAPI (Python 3.10+)
- Vector Database: ChromaDB
- AI Service: Google Gemini API
- Authentication: API Key-based
- Deployment: Uvicorn ASGI server

**Agent View (`/app_agent_view`)**
- Platform: Chrome Extension (Manifest V3)
- On-Device AI: Chrome Summarizer API, Chrome Rewriter API
- UI Framework: Vanilla JavaScript with HTML/CSS
- Storage: Chrome Local Storage API
- Communication: Fetch API for REST calls

**Leadership View (`/app_leadership_view`)**
- Framework: Streamlit (Python 3.10+)
- Visualization: Plotly, Altair
- Styling: Custom CSS for dark mode
- Data Refresh: Streamlit auto-refresh mechanism

## Components and Interfaces

### Backend API Components

#### 1. Chat Log Processor

**Purpose:** Analyzes historical chat logs and extracts knowledge for indexing.

**Key Classes:**
```python
class ChatLogProcessor:
    def __init__(self, gemini_client: GeminiClient, vector_db: VectorDatabase)
    def process_chat_logs(self, chat_logs: List[ChatMessage]) -> ProcessingResult
    def extract_knowledge(self, messages: List[ChatMessage]) -> List[KnowledgeEntry]
    def create_embeddings(self, knowledge_entries: List[KnowledgeEntry]) -> List[Embedding]
```

**Processing Flow:**
1. Receive batch of chat messages (max 100 per batch)
2. Send to Gemini API for knowledge extraction
3. Parse Gemini response to identify Q&A pairs, policies, and decisions
4. Generate vector embeddings for each knowledge entry
5. Store in Vector Database with metadata (timestamp, participants, source)

**Error Handling:**
- Log failures with timestamp and source identifier
- Implement retry logic for transient Gemini API errors
- Skip malformed messages and continue processing batch

#### 2. Query Service

**Purpose:** Handles natural language queries and retrieves relevant knowledge from Vector Database.

**Key Classes:**
```python
class QueryService:
    def __init__(self, vector_db: VectorDatabase, gemini_client: GeminiClient)
    def query_knowledge_base(self, query: str) -> QueryResult
    def generate_query_embedding(self, query: str) -> Embedding
    def search_similar_knowledge(self, embedding: Embedding, threshold: float = 0.7) -> List[KnowledgeMatch]
```

**Query Flow:**
1. Receive natural language query from client
2. Generate query embedding using Gemini API
3. Perform vector similarity search in ChromaDB
4. Filter results by similarity threshold (0.7)
5. Return top 3 matches with source metadata
6. Log query for trending topics analysis

**Response Format:**
```json
{
  "results": [
    {
      "content": "Policy answer text",
      "similarity_score": 0.85,
      "source": {
        "timestamp": "2024-11-10T14:30:00Z",
        "participants": ["user1", "user2"],
        "chat_id": "abc123"
      }
    }
  ],
  "query_id": "uuid",
  "timestamp": "2024-11-15T10:00:00Z"
}
```

#### 3. Vector Database Manager

**Purpose:** Manages ChromaDB operations including initialization, indexing, and persistence.

**Key Classes:**
```python
class VectorDatabase:
    def __init__(self, persist_directory: str)
    def initialize(self) -> None
    def add_knowledge(self, entries: List[KnowledgeEntry], embeddings: List[Embedding]) -> None
    def search(self, query_embedding: Embedding, top_k: int = 3, threshold: float = 0.7) -> List[Match]
    def persist(self) -> None
```

**Database Schema:**
- Collection: "knowledge_base"
- Document: Knowledge text content
- Embedding: 768-dimensional vector (Gemini embedding size)
- Metadata: timestamp, participants, source_id, chat_platform

**Performance Targets:**
- Query response time: < 1 second for 95% of queries
- Capacity: Support 10,000+ knowledge entries
- Persistence: Auto-save every 300 seconds

#### 4. API Endpoints

**POST /api/v1/chat-logs/process**
- Purpose: Submit chat logs for analysis
- Authentication: API Key required
- Request Body: Array of ChatMessage objects
- Response: ProcessingResult with success count and errors

**POST /api/v1/knowledge/query**
- Purpose: Query the knowledge base
- Authentication: API Key required
- Request Body: `{ "query": "natural language question" }`
- Response: QueryResult with matches and metadata

**GET /api/v1/metrics/queries**
- Purpose: Retrieve query logs for analytics
- Authentication: API Key required
- Query Params: `start_date`, `end_date`, `limit`
- Response: Array of query log entries

**GET /api/v1/metrics/unanswered**
- Purpose: Get unanswered questions from chat logs
- Authentication: API Key required
- Response: Array of unanswered question entries

**GET /api/v1/health**
- Purpose: Health check endpoint
- Authentication: None
- Response: `{ "status": "healthy", "vector_db": "connected" }`

### Agent View Components

#### 1. Content Script

**Purpose:** Runs on Teams web pages to detect text selection and inject UI elements.

**Key Modules:**
```javascript
// content.js
class TextSelectionHandler {
  constructor()
  detectSelection()
  showActionMenu(selectedText, position)
  hideActionMenu()
}

class ActionMenu {
  constructor(apiClient)
  render(position)
  handleSummarize(text)
  handleRephrase(text)
  handleQuery(text)
}
```

**Functionality:**
- Listen for text selection events on Teams pages
- Display floating action menu near selection
- Provide buttons for: Summarize, Rephrase, Query KB
- Handle user interactions and trigger appropriate AI operations

#### 2. Chrome AI Integration

**Purpose:** Interface with Chrome's built-in AI APIs for on-device processing.

**Key Modules:**
```javascript
// chrome-ai.js
class SummarizerService {
  async summarize(text)
  validateTextLength(text)
  handleError(error)
}

class RewriterService {
  async rephrase(text, tone = 'customer-friendly')
  validateTextLength(text)
  handleError(error)
}
```

**API Usage:**
- Summarizer API: `chrome.ai.summarizer.create()` then `summarize(text)`
- Rewriter API: `chrome.ai.rewriter.create({ tone: 'professional' })` then `rewrite(text)`
- Text length validation: 100-10,000 characters
- Timeout: 2 seconds for response display

#### 3. Backend API Client

**Purpose:** Communicate with Backend API for knowledge base queries.

**Key Modules:**
```javascript
// api-client.js
class BackendAPIClient {
  constructor(baseURL, apiKey)
  async queryKnowledgeBase(query)
  async retryRequest(request, maxRetries = 2)
  handleAuthError()
  handleNetworkError()
}
```

**Features:**
- API key authentication via header
- Exponential backoff retry (2 attempts)
- Error handling with user-friendly messages
- Loading state management (5-second timeout indicator)

#### 4. Extension Popup UI

**Purpose:** Provides standalone interface for knowledge base queries.

**Components:**
- Search input field
- Submit button
- Results display area with copy buttons
- Settings panel for API endpoint configuration
- Error message display

**UI Flow:**
1. User enters query in search field
2. Display loading indicator
3. Show results with source metadata
4. Provide copy-to-clipboard for each result
5. Handle errors gracefully with retry option

### Leadership View Components

#### 1. Metrics Dashboard

**Purpose:** Main dashboard displaying key performance indicators.

**Streamlit Layout:**
```python
# dashboard.py
def render_dashboard():
    st.title("Knowledge-Weaver Leadership Dashboard")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        render_response_time_metric()
    with col2:
        render_query_volume_metric()
    with col3:
        render_knowledge_gap_metric()
    
    render_unanswered_questions_section()
    render_trending_topics_section()
```

**Metrics Displayed:**
- Average Leadership Response Time (hours:minutes)
- Total Query Volume (last 7 days)
- Knowledge Gap Count (queries with no results)

**Refresh Rate:** 60 seconds for metrics, 300 seconds for trending analysis

#### 2. Unanswered Questions Tracker

**Purpose:** Display and track agent questions without responses.

**Data Source:** Backend API `/api/v1/metrics/unanswered`

**Display Format:**
```python
def render_unanswered_questions():
    questions = fetch_unanswered_questions()
    
    df = pd.DataFrame(questions)
    df = df.sort_values('age_hours', ascending=False)
    df = df.head(20)
    
    st.dataframe(df[['question', 'agent', 'age_hours', 'timestamp']])
```

**Columns:**
- Question text (truncated to 100 chars)
- Agent identifier
- Age in hours
- Original timestamp

#### 3. Trending Topics Analyzer

**Purpose:** Identify frequently queried topics and knowledge gaps.

**Analysis Logic:**
```python
def analyze_trending_topics(query_logs):
    # Extract topics from queries using keyword extraction
    topics = extract_topics(query_logs)
    
    # Count frequency
    topic_counts = Counter(topics)
    
    # Identify low-quality results
    gaps = identify_knowledge_gaps(query_logs)
    
    return {
        'top_topics': topic_counts.most_common(10),
        'knowledge_gaps': gaps
    }
```

**Visualization:**
- Bar chart for top 10 topics
- Table for knowledge gaps with query count and avg similarity score
- Highlight gaps in red where avg score < 0.5

#### 4. Dark Mode UI Theme

**Purpose:** Implement polished dark mode interface.

**CSS Styling:**
```css
/* custom_theme.css */
:root {
    --background-primary: #1a1a1a;
    --background-secondary: #2d2d2d;
    --text-primary: #e0e0e0;
    --text-secondary: #b0b0b0;
    --accent-primary: #6366f1;
    --accent-secondary: #8b5cf6;
    --border-color: #404040;
}

.metric-card {
    background: var(--background-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    color: var(--text-primary);
}
```

**Design Principles:**
- Minimum contrast ratio: 4.5:1
- Consistent spacing: 8px grid system
- Typography: Inter font family
- Visual hierarchy: Clear section headings with dividers

## Data Models

### ChatMessage

```python
@dataclass
class ChatMessage:
    id: str
    timestamp: datetime
    sender: str
    content: str
    platform: str  # e.g., "teams"
    thread_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### KnowledgeEntry

```python
@dataclass
class KnowledgeEntry:
    id: str
    content: str
    entry_type: str  # "qa", "policy", "decision"
    source_messages: List[str]  # Message IDs
    timestamp: datetime
    participants: List[str]
    confidence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### QueryResult

```python
@dataclass
class QueryResult:
    query_id: str
    query_text: str
    timestamp: datetime
    results: List[KnowledgeMatch]
    processing_time_ms: int

@dataclass
class KnowledgeMatch:
    knowledge_id: str
    content: str
    similarity_score: float
    source: SourceMetadata
    
@dataclass
class SourceMetadata:
    timestamp: datetime
    participants: List[str]
    chat_id: str
    platform: str
```

### UnansweredQuestion

```python
@dataclass
class UnansweredQuestion:
    question_id: str
    question_text: str
    agent: str
    timestamp: datetime
    age_hours: float
    thread_id: str
```

## Error Handling

### Backend API Error Handling

**Gemini API Failures:**
- Implement exponential backoff retry (3 attempts)
- Log error details with request context
- Return 503 Service Unavailable to clients
- Queue failed requests for later processing

**Vector Database Errors:**
- Catch ChromaDB exceptions during queries
- Return 500 Internal Server Error with generic message
- Log detailed error for debugging
- Implement health check to detect DB connectivity issues

**Authentication Errors:**
- Validate API key on every request
- Return 401 Unauthorized for invalid/missing keys
- Log authentication attempts for security monitoring

### Agent View Error Handling

**Chrome AI API Failures:**
- Display user-friendly error message
- Provide fallback option to use backend query
- Log error to console for debugging
- Check API availability on extension load

**Backend API Failures:**
- Retry with exponential backoff (2 attempts)
- Display error message with retry button
- Cache last successful results for offline reference
- Validate network connectivity before requests

**Text Selection Errors:**
- Validate text length before processing
- Show warning for text outside 100-10,000 char range
- Handle empty selections gracefully
- Prevent duplicate action menus

### Leadership View Error Handling

**Data Fetch Failures:**
- Display "Data unavailable" message in affected sections
- Retry fetch on next refresh cycle
- Log error details for investigation
- Maintain last successful data for display

**Visualization Errors:**
- Catch Plotly/Altair rendering exceptions
- Display fallback text-based data
- Log error with data context
- Validate data format before visualization

## Testing Strategy

### Backend API Testing

**Unit Tests:**
- Test ChatLogProcessor knowledge extraction logic
- Test QueryService embedding generation and search
- Test VectorDatabase CRUD operations
- Test API endpoint request/response handling
- Mock Gemini API calls for deterministic tests

**Integration Tests:**
- Test end-to-end chat log processing flow
- Test query flow from API endpoint to Vector DB
- Test authentication middleware
- Test error handling and retry logic
- Use test ChromaDB instance

**Performance Tests:**
- Benchmark query response times (target: <1s for 95%)
- Load test with 10,000 knowledge entries
- Test concurrent query handling
- Measure embedding generation throughput

### Agent View Testing

**Unit Tests:**
- Test TextSelectionHandler detection logic
- Test ActionMenu rendering and positioning
- Test SummarizerService and RewriterService
- Test BackendAPIClient retry logic
- Mock Chrome AI APIs

**Integration Tests:**
- Test content script injection on Teams pages
- Test end-to-end summarization flow
- Test end-to-end rephrasing flow
- Test end-to-end knowledge query flow
- Test extension popup UI interactions

**Manual Testing:**
- Test on live Teams web application
- Verify text selection detection accuracy
- Test UI responsiveness and positioning
- Verify copy-to-clipboard functionality
- Test across different Chrome versions

### Leadership View Testing

**Unit Tests:**
- Test metrics calculation functions
- Test trending topics analysis logic
- Test data transformation for visualizations
- Mock Backend API responses

**Integration Tests:**
- Test dashboard rendering with real data
- Test auto-refresh mechanism
- Test data fetch error handling
- Verify dark mode CSS application

**Visual Testing:**
- Verify contrast ratios meet 4.5:1 minimum
- Test layout responsiveness
- Verify chart rendering accuracy
- Test with various data volumes

### End-to-End Testing

**Scenario 1: Knowledge Resurrection Flow**
1. Submit historical chat logs to Backend API
2. Verify knowledge extraction and indexing
3. Query knowledge base from Agent View
4. Verify correct results returned
5. Check query logged for Leadership View

**Scenario 2: Agent Workflow**
1. Highlight text on Teams page
2. Summarize using Chrome AI
3. Rephrase for customer
4. Query knowledge base for policy
5. Copy result to clipboard

**Scenario 3: Leadership Monitoring**
1. View dashboard metrics
2. Check unanswered questions list
3. Analyze trending topics
4. Identify knowledge gaps
5. Verify data refresh

## Security Considerations

**API Key Management:**
- Store API keys in environment variables
- Never commit keys to version control
- Rotate keys periodically
- Use different keys for dev/prod environments

**Chrome Extension Security:**
- Request minimum required permissions
- Validate all user inputs
- Use Content Security Policy
- Store API endpoint in secure storage
- Sanitize text before display

**Data Privacy:**
- Do not log sensitive chat content
- Anonymize user identifiers in logs
- Implement data retention policies
- Provide data deletion capability
- Comply with data protection regulations

**Network Security:**
- Use HTTPS for all API communication
- Implement rate limiting on API endpoints
- Validate request origins
- Sanitize all inputs to prevent injection attacks
- Implement CORS policies

## Deployment Architecture

**Backend API Deployment:**
- Container: Docker image with Python 3.10
- Server: Uvicorn with 4 worker processes
- Reverse Proxy: Nginx for SSL termination
- Environment: Cloud VM or container service
- Persistence: Volume mount for ChromaDB data

**Agent View Distribution:**
- Package as Chrome Extension (.crx)
- Distribute via Chrome Web Store or enterprise policy
- Version management through manifest.json
- Auto-update enabled

**Leadership View Deployment:**
- Container: Docker image with Streamlit
- Port: 8501 (default Streamlit port)
- Access: Internal network or VPN
- Authentication: Optional Streamlit auth or reverse proxy auth

## Performance Optimization

**Backend API:**
- Cache frequently queried results (TTL: 300s)
- Batch chat log processing
- Use async/await for Gemini API calls
- Implement connection pooling for ChromaDB
- Index optimization for vector search

**Agent View:**
- Lazy load content script on Teams pages only
- Debounce text selection events (300ms)
- Cache Chrome AI API instances
- Minimize DOM manipulation
- Use efficient event listeners

**Leadership View:**
- Cache backend API responses (TTL: 60s)
- Lazy load visualizations
- Paginate large data tables
- Optimize Streamlit component rendering
- Use st.cache_data for expensive computations

## Monitoring and Observability

**Metrics to Track:**
- Backend API: Request rate, response time, error rate, Gemini API usage
- Agent View: Extension installs, feature usage, error rate
- Leadership View: Dashboard views, data refresh success rate
- System: Vector DB size, query latency, embedding generation time

**Logging:**
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Include request IDs for tracing
- Rotate logs daily
- Centralized log aggregation

**Alerting:**
- Alert on API error rate > 5%
- Alert on query latency > 2s
- Alert on Gemini API failures
- Alert on Vector DB connectivity issues
- Alert on extension crash rate > 1%
