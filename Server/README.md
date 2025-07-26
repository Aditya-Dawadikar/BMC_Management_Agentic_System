# Server: Telemetry Chat Assistant

This FastAPI server provides a chat endpoint that uses Google Gemini and MongoDB to answer telemetry-related questions for a given time window.

## Features

- Accepts natural language questions about telemetry data (e.g., "What were the telemetry issues on 24 July 2025?")
- Extracts date ranges using LLM and queries MongoDB for telemetry summaries
- Integrates with Google Gemini for natural language responses
- Logs the chat into MongoDB collection - chat_logs

## Requirements

Install dependencies with:

pip install -r requirements.txt

## Environment Variables

Create a .env file with this variables

S3_BUCKET_NAME=axiado-bmc
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION=us-east-2

MONGO_DB_NAME=bmc_telemetry_db
MONGO_COLLECTION_NAME=s3_telemetry_batches
MONGO_CHATLOGS_COLLECTION_NAME=chat_logs
MONGO_URI=mongodb+srv://bmc_user:booming@bmc-cluster.b6cjgoh.mongodb.net/?retryWrites=true&w=majority&appName=bmc-cluster&ssl=true

GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL_NAME=gemini-2.0-flash


## Running the server

uvicorn main:app --reload --host 0.0.0.0 --port 8002

## Testing on endpoint

Local endpoint: http://localhost:8002/chat

Body:
{
  "message": "What were the telemetry issues on 24 July 2025?"
}


