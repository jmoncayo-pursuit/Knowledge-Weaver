# Knowledge-Weaver Setup Guide

## Environment Setup (Completed)

The project now has a working Python 3.13 virtual environment with all dependencies installed.

### What Was Fixed

The original pip install failed because:
- **Python 3.13 compatibility**: Older versions of pydantic (2.6.0) and pydantic-core (2.16.1) were incompatible with Python 3.13's updated `ForwardRef._evaluate()` API
- **Solution**: Updated all dependencies to Python 3.13-compatible versions

### Updated Dependencies

**Backend API** (`backend_api/requirements.txt`):
- fastapi: 0.109.0 → >=0.115.0
- uvicorn: 0.27.0 → >=0.32.0
- chromadb: 0.4.22 → >=0.5.0
- google-generativeai: 0.3.2 → >=0.8.0
- pydantic: 2.6.0 → >=2.9.0 (includes pydantic-core 2.41.5 with Python 3.13 support)

**Leadership Dashboard** (`app_leadership_view/requirements.txt`):
- streamlit: 1.29.0 → >=1.40.0
- plotly: 5.18.0 → >=5.24.0
- pandas: 2.1.4 → >=2.2.0
- requests: 2.31.0 → >=2.32.0
- altair: 5.2.0 → >=5.5.0

## Quick Start

### Activate Virtual Environment
```bash
source venv/bin/activate
```

### Run Backend API
```bash
cd backend_api
uvicorn main:app --reload --port 8000
```

### Run Leadership Dashboard
```bash
cd app_leadership_view
streamlit run dashboard.py
```

### Environment Variables

Create a `.env` file in the `backend_api` directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
API_KEY=your_backend_api_key_here
```

## Next Steps

According to the tasks.md file, the following items are still pending:

### Backend API
- [ ] 9.1 Configure CORS middleware
- [ ] 9.2 Add global exception handlers
- [ ] 10.1 Implement periodic persistence task

### Chrome Extension
- [ ] 16.1 Implement settings management

### Leadership Dashboard
- [ ] 23.1 Create dashboard layout

### Integration and Documentation
- [ ] 24. Create sample data and testing utilities
- [ ] 25.1 Create Docker configuration for Backend API
- [ ] 25.2 Create Docker configuration for Leadership View

## Verification

All packages import successfully:
```bash
python -c "import fastapi, chromadb, google.generativeai, streamlit; print('✓ All packages imported successfully')"
```

## Populating the Database

After starting the backend, use the ingestion script to populate the database with sample data:

```bash
# Terminal 1: Start the backend
cd backend_api
source ../venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2: Run ingestion script
source venv/bin/activate
python ingest_sample_data.py
```

The script (`ingest_sample_data.py`) will:
- Check if the backend is running and healthy
- Load sample chat logs from `sample_chat_logs.json`
- Send them to the `/api/v1/chat-logs/process` endpoint in batches
- Display progress and results
- Exit with status 0 on success, 1 on failure

## Troubleshooting

If you encounter issues:
1. Ensure you're using Python 3.13: `python --version`
2. Recreate the virtual environment: `rm -rf venv && python3 -m venv venv`
3. Reinstall dependencies: `source venv/bin/activate && pip install -r backend_api/requirements.txt && pip install -r app_leadership_view/requirements.txt`
