# Knowledge-Weaver 🕸️

**Turning generic chat logs into a verified Source of Truth.**

Knowledge-Weaver is a "Human-in-the-Loop" system that captures valuable information from team chats, verifies it, and makes it instantly searchable. It bridges the gap between ephemeral conversations and permanent organizational knowledge.

## Architecture

The system uses a "Frankenstein" architecture, stitching together powerful components to create a seamless workflow:

```mermaid
graph TD
    subgraph "Frontend Layer"
        CE[Chrome Extension] -->|Capture & Search| API
        DB[Streamlit Dashboard] -->|Manage & Verify| API
    end

    subgraph "Backend Layer"
        API[FastAPI Backend] -->|Process Requests| S[Services]
        S -->|Vector Search| VDB[ChromaDB]
        S -->|AI Analysis| LLM[Gemini 2.5 Flash]
    end

    subgraph "Data Layer"
        VDB <-->|Store Embeddings| DISK[Persist Directory]
        LLM -->|Context & Few-Shot| VDB
    end

    style CE fill:#f9f,stroke:#333,stroke-width:2px
    style DB fill:#bbf,stroke:#333,stroke-width:2px
    style API fill:#dfd,stroke:#333,stroke-width:2px
    style VDB fill:#fdd,stroke:#333,stroke-width:2px
```

The system is styled with a **Custom Dark Theme** (configured in `.streamlit/config.toml`) to ensure a premium, consistent look across all components.

## 🤖 AI-Native Design

Knowledge-Weaver is built to be **Robot-Accessible** by design.
- **Stable Selectors**: All critical UI elements use `data-testid` attributes or stable keys, allowing AI agents (like the one building this!) to reliably navigate, test, and interact with the application.
- **Self-Verification**: The system includes automated verification scripts (`verify_roles.py`, `verify_recycle_bin.py`) that simulate user actions to ensure integrity.

## Key Features

### 1. Human-in-the-Loop Verification
AI is powerful, but not perfect. Knowledge-Weaver puts humans in control:
- **Capture**: AI suggests categories and tags from chat content.
- **Review**: Users verify and edit the AI's suggestions before saving.
- **Search**: Verified content is boosted in search results, ensuring reliability.

### 2. Active Learning (Dynamic Few-Shot Prompting)
The system gets smarter as you use it.
- When analyzing new content, the AI looks at **similar verified examples** from the vector database.
- This context helps the AI mimic your team's specific categorization style and tagging conventions.
- **Result**: The more you use it, the less you have to edit.

### 3. Gap-to-Gold
Identify and fill knowledge gaps in real-time.
- **Tracking**: The system tracks queries that return zero results.
- **Dashboard**: Leaders can see these "Knowledge Gaps" on the dashboard.
- **Bridge the Gap**: A dedicated UI allows experts to answer these missing questions directly, instantly turning a gap into a golden nugget of knowledge.

### 4. Recycle Bin (Soft Deletes)
Mistakes happen.
- **Safety**: Deleting an item performs a "soft delete," hiding it from search but keeping it in the database.
- **Recovery**: A dedicated "Recycle Bin" tab allows you to view and restore deleted items with a single click.

## Getting Started

### Prerequisites
- Python 3.13+
- Chrome Browser

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (API Keys)

### Running the System
1. **Backend**: `uvicorn backend_api.main:app --reload`
2. **Dashboard**: `streamlit run app_leadership_view/dashboard.py`
3. **Extension**: Load `app_extension` as an unpacked extension in Chrome.
