# Knowledge-Weaver Data Ingestion Guide

## Overview

The `ingest_sample_data.py` script is a one-time utility to populate your Knowledge-Weaver database with sample chat logs. It demonstrates the complete flow of processing historical chat data and extracting knowledge.

## Prerequisites

1. **Backend API running**: The backend must be running on `http://127.0.0.1:8000`
2. **Virtual environment activated**: `source venv/bin/activate`
3. **Sample data file**: `sample_chat_logs.json` must exist in the project root
4. **API key configured**: The backend must accept the API key `dev-secret-key-12345`

## Usage

### Basic Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run the script
python ingest_sample_data.py
```

### Step-by-Step Process

The script performs these steps automatically:

1. **Health Check** - Verifies the backend API is running and healthy
2. **Load Data** - Reads chat logs from `sample_chat_logs.json`
3. **Format Data** - Converts raw logs to the ChatMessage schema format
4. **Batch Processing** - Sends logs in batches of 100 messages
5. **Summary Report** - Displays success/failure counts and any errors

## Sample Output

```
============================================================
Knowledge-Weaver Data Ingestion Script
============================================================
Backend URL: http://127.0.0.1:8000
Sample data: sample_chat_logs.json
Timestamp: 2025-11-16T10:30:00
============================================================

[1/4] Checking backend health...
✓ Backend is healthy (status: healthy)
  Vector DB: connected

[2/4] Loading sample data...
✓ Loaded 12 messages from sample_chat_logs.json

[3/4] Formatting chat logs...
✓ Formatted 12 messages

[4/4] Ingesting data to backend...

📤 Sending batch 1/1 (12 messages)...
  ✓ Batch processed: 12 succeeded, 0 failed

============================================================
📊 INGESTION SUMMARY
============================================================
Total messages processed: 12
✓ Successfully processed: 12
✗ Failed: 0

============================================================
✅ INGESTION COMPLETED SUCCESSFULLY
============================================================

You can now:
  1. Query the knowledge base via the API
  2. Use the Chrome Extension to search
  3. View metrics in the Leadership Dashboard
```

## Configuration

You can modify these constants at the top of the script:

```python
BACKEND_URL = "http://127.0.0.1:8000"  # Backend API URL
API_KEY = "dev-secret-key-12345"        # API authentication key
SAMPLE_DATA_FILE = "sample_chat_logs.json"  # Input data file
```

## Error Handling

The script handles common errors gracefully:

### Backend Not Running
```
✗ Error: Cannot connect to backend at http://127.0.0.1:8000
  Make sure the backend is running:
  cd backend_api && uvicorn main:app --reload --port 8000
```

**Solution**: Start the backend API first

### File Not Found
```
✗ Error: File 'sample_chat_logs.json' not found
```

**Solution**: Ensure `sample_chat_logs.json` exists in the project root

### Authentication Failed
```
✗ Authentication failed: Invalid API key
```

**Solution**: Check that the API key in the script matches the backend configuration

### Batch Size Exceeded
```
✗ Bad request: Maximum 100 messages per batch
```

**Solution**: The script automatically handles batching, but if you modify it, ensure batches don't exceed 100 messages

## Data Format

The script expects JSON data in this format:

```json
[
  {
    "id": "msg_1",
    "timestamp": "2025-11-12T14:00:00",
    "sender": "Agent_1",
    "content": "Question about policy..."
  }
]
```

The script automatically adds:
- `platform`: "teams" (default)
- `thread_id`: null
- `metadata`: {}

## Testing the Ingestion

After successful ingestion, verify the data:

### 1. Query the API
```bash
curl -X POST http://127.0.0.1:8000/api/v1/knowledge/query \
  -H "X-API-Key: dev-secret-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the policy for address changes?"}'
```

### 2. Check Health Endpoint
```bash
curl http://127.0.0.1:8000/api/v1/health
```

Should show the vector database is connected and contains data.

### 3. Use the Chrome Extension
- Install the extension from `app_agent_view`
- Open the popup and search for topics from the sample data
- You should see relevant results

## Customizing for Your Data

To ingest your own chat logs:

1. **Prepare your data** in JSON format matching the schema
2. **Update the file path** in the script or pass it as an argument
3. **Adjust batch size** if needed (default: 100 messages)
4. **Run the script** with your data file

Example with custom file:
```python
# Modify the script
SAMPLE_DATA_FILE = "my_custom_logs.json"
```

## Troubleshooting

### Script hangs during ingestion
- Check backend logs for errors
- Verify Gemini API key is configured
- Ensure sufficient API quota

### Partial success (some messages failed)
- Review error messages in the summary
- Check message format matches schema
- Verify timestamp format is ISO 8601

### No results when querying
- Wait a few seconds for indexing to complete
- Check that embeddings were generated successfully
- Verify vector database persistence

## Next Steps

After successful ingestion:

1. **Test queries** using the API or Chrome Extension
2. **View metrics** in the Leadership Dashboard
3. **Add more data** by running the script with additional files
4. **Monitor performance** using the health endpoint

## Support

For issues or questions:
- Check backend logs: Look for errors during processing
- Review API documentation: See `README.md` for endpoint details
- Verify configuration: Ensure all environment variables are set
