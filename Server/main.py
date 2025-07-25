import os
import json
from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
import google.generativeai as genai
from dotenv import load_dotenv
from redfish_agent import get_agent_response
import traceback

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "bmc_telemetry_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "s3_telemetry_batches")

# Mongo Setup
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
mongo_collection = mongo_db[MONGO_COLLECTION_NAME]

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

def iso_to_unix(iso_str):
    return int(datetime.fromisoformat(iso_str).timestamp())

def extract_date_range(text: str) -> tuple[str | None, str | None]:
    
    # TODO: Update prompt to find is S3 source is needed. Add one var in return statement as True or False for S3 source

    prompt = f"""
        Extract the start and end dates from the following sentence:
        "{text}"
        today is {datetime.now(timezone.utc).date().isoformat()}
        Return a valid JSON object using ISO 8601 date format (YYYY-MM-DDTHH:MM:SS).
        If only one date is found, set start_date from 00:00:00 and end_date till 23:59:59.

        Respond only with:
        {{
        "start_date": "YYYY-MM-DDTHH:MM:SS",
        "end_date": "YYYY-MM-DDTHH:MM:SS"
        }}
        No explanations, markdown, or extra text.
        """
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    response = model.generate_content(prompt)
    
    content = response.text.strip().strip("```json").strip("```")

    try:
        data = json.loads(content)
        start_date = data.get("start_date")
        end_date = data.get("end_date") or start_date  # handle single-date case
        return start_date, end_date
    except json.JSONDecodeError:
        return None, None

@app.post("/test")
async def test(request: ChatRequest):
    try:
        user_message = request.message
        reply = await get_agent_response(user_message)
        return {"response": reply}
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message

    # Step 1: Extract time window & identify if S3 source is needed
    # TODO: accept three return values.
    start_iso, end_iso = extract_date_range(user_message)
    print("Dates from LLM:",start_iso, end_iso)
    if not start_iso:
        return {"response": "Sorry, I couldn't understand the date in your question."}

    # Step 2: Query Mongo for overlapping summaries & S3 locations
    # TODO: Get S3 path based on the variable
    start_unix = iso_to_unix(start_iso)
    end_unix = iso_to_unix(end_iso)
    print("Dates for Mongo:",start_unix, end_unix)
    summaries = mongo_collection.find({
        "end_time": {"$gte": str(start_unix)},
        "start_time": {"$lte": str(end_unix)}
    })

    summary_list = list(summaries)
    print(summary_list)

    # TODO: If S3 source is needed, query S3 for telemetry files in the date range

    # Step 3: Prepare context
    # TODO: Add S3 data if needed
    if not summary_list:
        context = "No telemetry data found in that time range."
    else:
        context = "\n".join([
            f"[{s['start_time']} - {s['end_time']}] Threats: {s['threat_count']}, Unhealthy: {s['unhealthy_count']}, Reasons: {json.dumps(s['reasons'])}"
            for s in summary_list
        ])

    # Step 4: Build prompt & call Gemini
    prompt = (
        f"You are a system telemetry assistant. A user asked:\n\n"
        f"{user_message}\n\n"
        f"Here is the telemetry summary for the relevant time range:\n{context}\n\n"
        "Please analyze and answer clearly."
    )
    print(f"Prompt sent to Gemini:\n{prompt}\n")
    try:
        chat = gemini_model.start_chat()
        response = chat.send_message(prompt)
        reply = response.text
    except Exception as e:
        reply = f"Gemini error: {e}"

    return {"response": reply}
