# Server: Telemetry Chat Assistant

This FastAPI server provides a chat endpoint that uses Google Gemini and MongoDB to answer telemetry-related questions for a given time window.

## Features

- Accepts natural language questions about telemetry data (e.g., "What were the telemetry issues on 24 July 2025?")
- Extracts date ranges using LLM and queries MongoDB for telemetry summaries
- Integrates with Google Gemini for natural language responses
- Logs the chat into MongoDB collection - `chat_logs`
- Logs the actions into MongoDB collection - `action_logs`
- Supports S3 integration for fetching telemetry files
- Automates Redfish API actions for telemetry management

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file with the following variables:

```properties
S3_BUCKET_NAME=axiado-bmc
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION=us-east-2

MONGO_DB_NAME=bmc_telemetry_db
MONGO_COLLECTION_NAME=s3_telemetry_batches
MONGO_CHAT_LOGS_COLLECTION_NAME=chat_logs
MONGO_URI=<MONGO CONNECTION STRING>
MONGO_S3_TELEMETRY_COLLECTION_NAME=s3_telemetry_batches
MONGO_ACTION_LOGS_COLLECTION_NAME=action_logs

GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL_NAME=gemini-2.0-flash
```

## Running the server

uvicorn main:app --reload --host 0.0.0.0 --port 8002

## Testing on endpoint

Local endpoint: http://localhost:8002/chat (POST)

Body:
{
  "message": "What were the telemetry issues on 24 July 2025?"
}


Local endpoint: http://localhost:8002/api/action_logs (GET)

```
query:
{ "actor": "agent/user" }

query:
{ "endpoint": "http://localhost:8001/redfish/v1/Chassis/Chassis-1/Thermal/Fans" }

query:
{ "payload.Fan1": 50 }

query:
{ "actor": "agent", "endpoint": "http://localhost:8001/redfish/v1/Chassis/Chassis-1/Thermal/Fans" }
```

after some timestamp:
```
query:
{ "timestamp": { "$gte": "2025-07-24T12:00:00" } }
```

before some time:
```
query:
{ "timestamp": { "$lte": "2025-07-24T12:00:00" } }
```

between dates:
```
query:
{ "timestamp": { "$gte": "2025-07-25T00:00:00", "$lte": "2025-07-27T23:59:59" } }
```




