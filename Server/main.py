import os
import json
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from pydantic import BaseModel
from pymongo import MongoClient
import google.generativeai as genai
from dotenv import load_dotenv
import boto3
from fastapi.middleware.cors import CORSMiddleware
from redfish_agent import get_agent_response
import traceback
from fastapi.responses import JSONResponse
from mongo_crud.mongo_crud import get_action_logs, insert_chat_log, get_summaries, get_recent_chat_messages


load_dotenv()
# Configs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)

# S3 setup
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ChatRequest(BaseModel):
    message: str

def iso_to_unix(iso_str):
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return int(dt.timestamp())

def extract_date_range(text: str):
    prompt = f"""
    You are a system assistant that extracts time ranges and identifies whether raw S3 telemetry logs are required.

    Here is a user query:
    "{text}"

    Today's date is {datetime.now(timezone.utc).date().isoformat()}.

    Respond in this JSON format ONLY:
    {{
    "start_date": "YYYY-MM-DDTHH:MM:SS",
    "end_date": "YYYY-MM-DDTHH:MM:SS",
    "s3_required": true/false
    }}

    Rules:
    - If the user mentions **sensor-level data**, like fan speeds, temperatures, CPU/GPU stats, or detailed logs → `s3_required = true`
    - If the user just asks for **health summaries**, threat counts, or high-level summaries → `s3_required = false`
    - If only one date is found, set `start_date` to 00:00:00 and `end_date` to 23:59:59 of that day.

    Respond with JSON only. No extra text, no markdown.
    """
    response = genai.GenerativeModel(GEMINI_MODEL_NAME).generate_content(prompt)
    content = response.text.strip().strip("```json").strip("```")
    try:
        data = json.loads(content)
        return data.get("start_date"), data.get("end_date") or data.get("start_date"), data.get("s3_required", False)
    except json.JSONDecodeError:
        return None, None, False

def fetch_s3_data(s3_path: str) -> str:
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_path)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching from S3: {e}")
        return "Error fetching telemetry file from S3."
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
    # Step 1: Extract window and s3 flag
    start_iso, end_iso, s3_needed = extract_date_range(user_message)
    print("Dates from LLM:", start_iso, end_iso, ", S3 Needed:", s3_needed)
    if not start_iso:
        return {"response": "Sorry, I couldn't understand the date in your question."}
    start_unix = iso_to_unix(start_iso)
    end_unix = iso_to_unix(end_iso)
    print("Dates for Mongo:", start_unix, end_unix)
    
    # Fetch summaries from MongoDB
    summary_list = get_summaries(start_unix, end_unix)

    if not summary_list:
        context = "No telemetry data found in that time range."
        s3_data = ""
    else:
        context = "\n".join([
            f"[{s['start_time']} - {s['end_time']}] Threats: {s['threat_count']}, Unhealthy: {s['unhealthy_count']}, Reasons: {json.dumps(s['reasons'])}"
            for s in summary_list
        ])
        s3_data = ""
        if s3_needed:
            for s in summary_list:
                s3_path = s.get("s3_path")
                if s3_path:
                    file_data = fetch_s3_data(s3_path)
                    s3_data += f"\n\nS3 Telemetry File ({s3_path}):\n{file_data[:1000]}"
                    print(s3_data)
        
    prompt = (
        f"You are a system telemetry assistant. A user asked:\n\n"
        f"{user_message}\n\n"
        f"Here is the telemetry summary for the relevant time range:\n{context}\n\n"
        f"{s3_data}\n"
        "Please analyze and answer clearly."
    )
    try:
        chat = gemini_model.start_chat()
        response = chat.send_message(prompt)
        reply = response.text
        insert_chat_log(
            user_message=user_message,
            ai_response=reply,
            date_range={"start": start_iso, "end": end_iso},
            s3_used=s3_needed
        )
    except Exception as e:
        reply = f"Gemini error: {e}"
    return {"response": reply}


@app.get("/api/chat_messages/recent")
def get_chat_messages():
    return get_recent_chat_messages()

@app.get("/api/action_logs")
def fetch_action_logs(request: Request, limit: int = 10):
    """
    API endpoint to fetch action logs.
    :param request: The HTTP request object to extract the query parameter.
    :param limit: Maximum number of records to return.
    :return: JSONResponse containing the action logs.
    """
    query_param = request.query_params.get("query")
    query = json.loads(query_param) if query_param else None
    print("Parsed Query:", query)  # Debugging log
    return get_action_logs(query=query, limit=limit)