from pymongo import MongoClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import certifi
from fastapi.responses import JSONResponse

load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "bmc_telemetry_db")
MONGO_CHAT_LOGS_COLLECTION_NAME = os.getenv("MONGO_CHAT_LOGS_COLLECTION_NAME", "chat_logs")
MONGO_ACTION_LOGS_COLLECTION_NAME = os.getenv("MONGO_ACTION_LOGS_COLLECTION_NAME", "action_logs")
MONGO_S3_TELEMETRY_COLLECTION_NAME = os.getenv("MONGO_S3_TELEMETRY_COLLECTION_NAME", "s3_telemetry")

mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
mongo_db = mongo_client[MONGO_DB_NAME]
mongo_chat_logs = mongo_db[MONGO_CHAT_LOGS_COLLECTION_NAME]
mongo_action_logs = mongo_db[MONGO_ACTION_LOGS_COLLECTION_NAME]

def insert_chat_log(user_message: str, ai_response: str, date_range: dict, s3_used: bool):
    """
    Inserts a chat log into the MongoDB chat_logs collection.
    """
    mongo_chat_logs.insert_one({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_message": user_message,
        "ai_response": ai_response,
        "date_range": date_range,
        "s3_used": s3_used
    })

def log_action(actor: str, endpoint: str, payload: dict, response: dict):
    """
    Logs the action into MongoDB.
    actor: who performed the action (e.g., "agent", "user")
    endpoint: Redfish API endpoint called
    payload: request payload
    response: response from the Redfish API
    """
    mongo_action_logs.insert_one({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "endpoint": endpoint,
        "payload": payload,
        "response": response,
    })

def get_summaries(start_unix: int, end_unix: int):
    """
    Fetch summaries from MongoDB based on the given time range.
    """
    return list(mongo_db[MONGO_S3_TELEMETRY_COLLECTION_NAME].find({
        "end_time": {"$gte": str(start_unix)},
        "start_time": {"$lte": str(end_unix)}
    }))

def get_recent_chat_messages():
    """
    Fetch the most recent chat messages from the MongoDB chat_logs collection.
    The messages are sorted in descending order of timestamp, and the result is limited to 10 records.
    :return: A JSONResponse containing the recent chat messages or an error message.
    """
    try:
        logs = list(mongo_chat_logs.find().sort("timestamp", -1).limit(10))
        print("Returning logs:", logs)  # Add this line
        for log in logs:
            log["_id"] = str(log["_id"])
        return JSONResponse(content={"messages": logs})
    except Exception as e:
        print("Error fetching chat logs:", e)  # Add this line
        return JSONResponse(content={"error": str(e)}, status_code=500)

def get_action_logs(query: dict = None, limit: int = 20):
    """
    Fetch records from the action_logs collection based on the given query.
    :param query: A dictionary representing the MongoDB query filter.
    :param limit: The maximum number of records to return (default: 10).
    :return: A JSONResponse containing the action logs or an error message.
    """
    try:
        if query is None:
            query = {}  # Default to an empty query to fetch all records

        logs = list(mongo_action_logs.find(query).sort("timestamp", -1).limit(limit))
        print("Returning action logs:", logs)  # Debugging log
        for log in logs:
            log["_id"] = str(log["_id"])  # Convert ObjectId to string for JSON serialization
        return JSONResponse(content={"action_logs": logs})
    except Exception as e:
        print("Error fetching action logs:", e)  # Debugging log
        return JSONResponse(content={"error": str(e)}, status_code=500)
