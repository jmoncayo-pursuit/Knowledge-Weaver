# Knowledge-Weaver

**Resurrect dead knowledge from chat logs and transform it into a living, queryable knowledge base.**

## The Problem

Organizations lose critical knowledge every day. Important decisions, policy clarifications, and procedural guidance get buried in chat logs on platforms like Microsoft Teams. When agents need answers, they either:
- Waste time searching through endless chat history
- Ask leadership the same questions repeatedly
- Make decisions without complete information

This creates inefficiency, inconsistency, and knowledge gaps that impact customer service quality.

## The Solution

Knowledge-Weaver is a hybrid AI system that combines cloud-based and on-device AI to resurrect knowledge from unstructured chat logs. The system consists of three integrated applications:

1. **Backend API** - Analyzes chat logs using Google Gemini AI, extracts knowledge, and stores it in a vector database for semantic search
2. **Agent View** - Chrome Extension that provides AI-powered tools directly in Microsoft Teams (summarization, rephrasing, knowledge base queries)
3. **Leadership View** - Real-time dashboard for monitoring team performance and identifying knowledge gaps

## Features

### For Agents
- **Text Summarization** - Quickly summarize long chat conversations using Chrome's built-in AI
- **Text Rephrasing** - Convert internal notes to customer-friendly language
- **Knowledge Base Search** - Query the centralized knowledge base for policy answers and past decisions
- **Seamless Integration** - Works directly within Microsoft Teams web interface

### For Leadership
- **Live Metrics** - Monitor query volume, response times, and knowledge gaps
- **Unanswered Questions Tracking** - Identify questions that need attention
- **Trending Topics Analysis** - See what agents are asking about most frequently
- **Auto-Refresh Dashboard** - Real-time updates every 60 seconds

### Technical Features
- **HIPAA Compliance** - Automatic anonymization of sensitive data before processing
- **Hybrid AI Architecture** - Combines on-device Chrome AI with cloud-based Gemini AI
- **Vector Search** - Semantic similarity search for finding relevant knowledge
- **RESTful API** - Clean, documented API for integration

## Architecture

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

## Installation

### Prerequisites
- Python 3.10+
- Node.js (for development)
- Google Gemini API key
- Chrome browser (version 127+ for AI features)

### Backend API Setup

1. Navigate to the backend directory:
```bash
cd backend_api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
BACKEND_API_KEY=your_secure_api_key_here
```

4. Start the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Chrome Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `app_agent_view` directory
5. The extension icon will appear in your toolbar

### Leadership Dashboard Setup

1. Navigate to the dashboard directory:
```bash
cd app_leadership_view
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.streamlit/secrets.toml`:
```toml
BACKEND_API_URL = "http://localhost:8000"
BACKEND_API_KEY = "your_secure_api_key_here"
```

4. Start the dashboard:
```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## How to Use

### Quick Start: Ingest Sample Data

The easiest way to populate your database with sample data:

1. Make sure the backend is running:
```bash
cd backend_api
source ../venv/bin/activate
uvicorn main:app --reload --port 8000
```

2. In a new terminal, run the ingestion script:
```bash
source venv/bin/activate
python ingest_sample_data.py
```

The script will:
- Check backend health
- Load sample chat logs from `sample_chat_logs.json`
- Process and ingest them into the vector database
- Display a summary of the ingestion results

### Processing Chat Logs (Manual)

You can also manually process chat logs via the API:

```bash
curl -X POST http://localhost:8000/api/v1/chat-logs/process \
  -H "X-API-Key: dev-secret-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_logs": [
      {
        "id": "msg1",
        "timestamp": "2024-11-15T10:00:00Z",
        "sender": "agent1",
        "content": "What is our refund policy?",
        "platform": "teams"
      },
      {
        "id": "msg2",
        "timestamp": "2024-11-15T10:05:00Z",
        "sender": "manager",
        "content": "Our refund policy allows 30 days for returns...",
        "platform": "teams"
      }
    ]
  }'
```

### Using the Chrome Extension

1. Navigate to Microsoft Teams web interface
2. Highlight any text in a chat
3. Click one of the action buttons:
   - **Summarize** - Get a quick summary
   - **Rephrase** - Convert to customer-friendly language
   - **Query KB** - Search the knowledge base

4. Or click the extension icon to open the popup and search directly

### Monitoring with the Dashboard

1. Open the Leadership Dashboard
2. View real-time metrics:
   - Query volume trends
   - Response time averages
   - Knowledge gap identification
3. Review unanswered questions that need attention
4. Analyze trending topics to prioritize knowledge base improvements

## Technology Stack

- **Backend**: Python, FastAPI, ChromaDB, Google Gemini AI
- **Agent View**: JavaScript, Chrome Extension API, Chrome AI APIs
- **Leadership View**: Python, Streamlit, Plotly, Pandas
- **Database**: ChromaDB (vector database)
- **AI**: Google Gemini (cloud), Chrome AI (on-device)

## Security & Compliance

- **HIPAA Compliance**: Automatic anonymization of PII before sending to external APIs
- **API Key Authentication**: Secure access control for all endpoints
- **Data Privacy**: Sensitive information is redacted (emails, phone numbers, SSNs, IDs)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
