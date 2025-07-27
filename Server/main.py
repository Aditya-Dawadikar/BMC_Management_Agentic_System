import os
import json
from datetime import datetime, timezone
import boto3
import json
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import HTTPException
from pydantic import BaseModel

from mongo_crud.mongo_crud import get_action_logs, insert_chat_log, get_summaries, get_recent_chat_messages, authenticate_user
from log_manager import sse_stream, stop_stream

from redfish_agent import get_agent_response
from chatbot_agent import get_chatbot_response
from preprocessor_agent import get_preprocessor_response
from query_router_agent import get_query_router_response

load_dotenv()

# Configs
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

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

log_buffer = []
MAX_BUFFER = 1000
FLUSH_INTERVAL_MS = 500
shutdown_flag = False


#===============================================
# CHAT MESSAGES
#===============================================
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        user_message = request.message
        
        query_metadata = await get_query_router_response(user_message)

        print("router response: ", query_metadata)

        if query_metadata.get("query_type") == "UNKNOWN":
            insert_chat_log(
                    user_message=user_message,
                    ai_response=query_metadata.get("response")
                )
            return {"response": query_metadata.get("response")}
        elif query_metadata.get("query_type") == "ACTION":
            reply = await get_agent_response(user_message)

            insert_chat_log(
                    user_message=user_message,
                    ai_response=reply.get("action_summary")
                )

            return {"response": reply.get("action_summary")}
        elif query_metadata.get("query_type") == "INFERENCE":
            # Step 1: Extract window and s3 flag
            start_iso, end_iso, s3_needed = await extract_date_range(user_message)
            if not start_iso:
                reply = "Sorry, I couldn't understand the date range in your question."
                insert_chat_log(
                    user_message=user_message,
                    ai_response=reply
                )
                return {"response": reply}

            start_unix = iso_to_unix(start_iso)
            end_unix = iso_to_unix(end_iso)

            print(start_unix, end_unix, type(start_unix), type(end_unix))
            
            # Fetch summaries from MongoDB
            summary_list = get_summaries(start_unix, end_unix)

            print(summary_list)

            if not summary_list:
                context = "No telemetry data found in that time range."
                s3_data = ""
            else:
                context = "\n".join([
                    f"[{s['start_time']} - {s['end_time']}] Threats: {s['threat_count']}, Unhealthy: {s['unhealthy_count']}, Reasons: {json.dumps(s['reasons'])}"
                    for s in summary_list
                ])

                print(context)

                s3_data = ""
                # if s3_needed:
                #     for s in summary_list:
                #         s3_path = s.get("s3_path")
                #         if s3_path:
                #             file_data = fetch_s3_data(s3_path)
                #             s3_data += f"\n\nS3 Telemetry File ({s3_path}):\n{file_data}"

                for s in summary_list:
                    s3_path = s.get("s3_path")
                    if s3_path:
                        file_data = fetch_s3_data(s3_path)
                        s3_data += f"\n\nS3 Telemetry File ({s3_path}):\n{file_data}"

            print(s3_data)

            reply = await get_chatbot_response(user_message, context, s3_data)

            print("AI: ", reply)

            insert_chat_log(
                    user_message=user_message,
                    ai_response=reply,
                    date_range={"start": start_iso, "end": end_iso},
                    s3_used=s3_needed
                )
                
            return {"response": reply}
            
        else:
            raise HTTPException(status_code=500, detail="Routing Agent returned malformed reponse. try again")
    except Exception as e:
                reply = f"Error: {e}"

@app.get("/api/chat_messages/recent")
def get_chat_messages():
    return get_recent_chat_messages()

#===============================================
# APPLICATION LOGS
#===============================================
@app.get("/logs")
async def logs_stream(request: Request):
    return StreamingResponse(sse_stream(request), media_type="text/event-stream")

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


#===============================================
# APP Events
#===============================================

@app.on_event("shutdown")
async def shutdown_event():
    stop_stream()

#===============================================
# UTILS
#===============================================
def iso_to_unix(iso_str):
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return int(dt.timestamp())

async def extract_date_range(text: str):
    try:
        response = await get_preprocessor_response(text, datetime.now(timezone.utc).date().isoformat())
        print("Preprocessor response:", response)
        content = response.strip().strip("```json").strip("```")
    
        data = json.loads(content)
        return data.get("start_date"), data.get("end_date") or data.get("start_date"), data.get("s3_required", False)
    except json.JSONDecodeError:
        return None, None, False
    except Exception as e:
        reply = f"Error: {e}"

def fetch_s3_data(s3_path: str) -> str:
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_path)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching from S3: {e}")
        return "Error fetching telemetry file from S3."

#===============================================
# TEST CODE
#===============================================

# @app.post("/log")
# async def add_log(log: dict):
#     push_log(log)
#     return {"status": "queued", "message": log}

# @app.post("/test")
# async def test(request: ChatRequest):
#     try:
#         user_message = request.message
#         reply = await get_agent_response(user_message)
#         return {"response": reply}
#     except Exception as e:
#         traceback.print_exc()
#         return {"error": str(e)}

@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    password = data.get("password")
    user = authenticate_user(user_id, password)
    if user:
        return JSONResponse({"success": True, "user_id": user_id})
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
