# Server: Telemetry Chat Assistant

This FastAPI server provides a chat endpoint that uses Google Gemini and MongoDB to answer telemetry-related questions for a given time window.

## Features

- Accepts natural language questions about telemetry data (e.g., "What were the telemetry issues on 24 July 2025?")
- Extracts date ranges using LLM and queries MongoDB for telemetry summaries
- Integrates with Google Gemini for natural language responses

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
MONGO_URI=mongodb://localhost:27017/

GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL_NAME=gemini-2.0-flash


## Running the server

uvicorn main:app --reload

## Testing on endpoint

Local endpoint: http://localhost:8000/chat

Body:
{
  "message": "What were the telemetry issues on 24 July 2025?"
}


