import os
from fastapi import FastAPI, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
import requests
import asyncio
import threading, time, json, boto3
from datetime import datetime
from botocore.exceptions import BotoCoreError, NoCredentialsError
from dotenv import load_dotenv
from pymongo import MongoClient

from redfish_controller import get_snapshot

load_dotenv()

# Setup S3
s3_buffer = []
s3_bucket_name = os.getenv("S3_BUCKET_NAME")
s3_prefix = "telemetry/"
s3 = boto3.client("s3")

background_task = None

PROBE_INTERVAL = int(os.getenv("PROBE_INTERVAL",5)) # 2secs
BATCH_SIZE = int(os.getenv("BATCH_SIZE",5)) # 10 records

# Setup MongoDB
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_db_name = os.getenv("MONGO_DB_NAME", "bmc_telemetry_db")
mongo_collection_name = os.getenv("MONGO_COLLECTION_NAME", "s3_telemetry_batches")

mongo_client = MongoClient(mongo_uri)
mongo_db = mongo_client[mongo_db_name]
mongo_collection = mongo_db[mongo_collection_name]

app = FastAPI()

LIBRE_HARDWARE_MONITORING_ENDPOINT = os.getenv("LIBRE_HARDWARE_MONITORING_ENDPOINT")

DEVICE_NAME=os.getenv("DEVICE_NAME")
MODULES_TO_MONITOR=os.getenv("MODULES_TO_MONITOR")

# Define Gauges

cpu_temp_gauge = Gauge("cpu_temperature_celsius", "CPU Temperature", ["chassis", "sensor"])
cpu_min_temp_gauge = Gauge("cpu_min_temperature_celsius", "CPU Temperature (Min)", ["chassis", "sensor"])
cpu_max_temp_gauge = Gauge("cpu_max_temperature_celsius", "CPU Temperature (Max)", ["chassis", "sensor"])

cpu_voltage_gauge = Gauge("cpu_voltage_volt", "CPU Voltage", ["chassis", "rail"])
cpu_powers_gauge = Gauge("cpu_powers_watt", "CPU Power", ["chassis", "supply"])
cpu_load_gauge = Gauge("cpu_load_percent", "CPU Load", ["chassis", "core"])


def classify_snapshot(snapshot):
    reasons = []
    status = "healthy"

    for chassis in snapshot.get("Chassis", []):
        chassis_id = chassis.get("Id", "Unknown")

        # --- Temperature checks ---
        thermal = chassis.get("Thermal", {})
        for temp in thermal.get("Temperatures", []):
            name = temp.get("Name", "Unknown")
            value = temp.get("ReadingCelsius", 0)
            sensor_name = f"{chassis_id}:{name}"

            if value > 90:
                reasons.append(f"Temperature too high on '{sensor_name}' ({value}°C > 90°C)")
            elif value > 80:
                reasons.append(f"Temperature elevated on '{sensor_name}' ({value}°C > 80°C)")

        # --- Voltage checks ---
        for voltage in chassis.get("Voltages", []):
            name = voltage.get("Name", "Unknown")
            value = voltage.get("ReadingVolts", 0)
            sensor_name = f"{chassis_id}:{name}"

            if value > 1.6:
                reasons.append(f"Voltage too high on '{sensor_name}' ({value}V > 1.6V)")

        # --- Power checks ---
        power = chassis.get("Power", {})
        total_power = power.get("PowerConsumedWatts", 0)
        if total_power > 80:
            reasons.append(f"Power draw is critical on '{chassis_id}:Total' ({total_power}W > 80W)")
        elif total_power > 50:
            reasons.append(f"Power draw is elevated on '{chassis_id}:Total' ({total_power}W > 50W)")

        for psu in power.get("PowerSupplies", []):
            name = psu.get("Name", "Unknown")
            capacity = psu.get("CapacityWatts", 0)
            sensor_name = f"{chassis_id}:{name}"
            if capacity > 80:
                reasons.append(f"Power draw is critical on '{sensor_name}' ({capacity}W > 80W)")
            elif capacity > 50:
                reasons.append(f"Power draw is elevated on '{sensor_name}' ({capacity}W > 50W)")

    # Determine status
    if any("too high" in r or "critical" in r for r in reasons):
        status = "threat"
    elif reasons:
        status = "unhealthy"

    return status, reasons


async def update_metrics():
    """
    Update Prometheus gauges based on the snapshot JSON data.
    snapshot_json can be a Python dict or a JSON string.
    """
    try:
        data = get_snapshot()
        
        print(f"[{datetime.utcnow().isoformat()}] Snapshot collected")

        for chassis in data.get("Chassis", []):
            chassis_id = chassis.get("Id")

            # Update thermal metrics
            thermal = chassis.get("Thermal", {})
            for temp_sensor in thermal.get("Temperatures", []):
                name = temp_sensor.get("Name", "Unknown")
                current_temp = temp_sensor.get("ReadingCelsius", 0)
                cpu_temp_gauge.labels(chassis=chassis_id, sensor=name).set(current_temp)
                cpu_min_temp_gauge.labels(chassis=chassis_id, sensor=name).set(temp_sensor.get("LowerThresholdNonCritical", 0))
                cpu_max_temp_gauge.labels(chassis=chassis_id, sensor=name).set(temp_sensor.get("UpperThresholdCritical", 0))

            # Update voltage metrics
            for voltage in chassis.get("Voltages", []):
                rail_name = voltage.get("Name", "Unknown")
                cpu_voltage_gauge.labels(chassis=chassis_id, rail=rail_name).set(voltage.get("ReadingVolts", 0))

            # Update power metrics
            power = chassis.get("Power", {})
            total_power = power.get("PowerConsumedWatts", 0)
            cpu_powers_gauge.labels(chassis=chassis_id, supply="Total").set(total_power)

            for supply in power.get("PowerSupplies", []):
                supply_name = supply.get("Name", "Unknown")
                capacity = supply.get("CapacityWatts", 0)
                cpu_powers_gauge.labels(chassis=chassis_id, supply=supply_name).set(capacity)

        return data

    except Exception as e:
        print(f"Error fetching metrics: {e}")

# Expose /metrics
@app.get("/metrics")
async def metrics():
    await update_metrics()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.on_event("startup")
async def start_background_thread():
    global background_task
    background_task = asyncio.create_task(background_collector())

def to_unix_timestamp(ts: str) -> str:
    return str(int(datetime.fromisoformat(ts).timestamp()))

def summarize_batch(buffer, s3_path, start_time, end_time):
    summary = {
        "s3_path": s3_path,
        "start_time": start_time,
        "end_time": end_time,
        "total_records": len(buffer),
        "threat_count": 0,
        "unhealthy_count": 0,
        "healthy_count": 0,
        "reasons": []  # list of {timestamp, reason}
    }

    for record in buffer:
        status = record.get("health_status", "healthy")
        timestamp = record.get("timestamp", "unknown")
        reasons = record.get("reasons", [])

        if status == "threat":
            summary["threat_count"] += 1
        elif status == "unhealthy":
            summary["unhealthy_count"] += 1
        else:
            summary["healthy_count"] += 1

        for reason in reasons:
            summary["reasons"].append({
                "timestamp": timestamp,
                "reason": reason
            })

    return summary

async def background_collector():
    global s3_buffer
    batch_start_time = None
    print("[BackgroundCollector] Started")

    try:
        while True:
            await asyncio.sleep(PROBE_INTERVAL)

            try:
                snapshot = await update_metrics()  # Remove await if update_metrics is not async
            except TypeError as e:
                print(f"Error fetching metrics: {e}")
                snapshot = None

            if snapshot:
                if batch_start_time is None:
                    batch_start_time = to_unix_timestamp(snapshot["timestamp"])
                s3_buffer.append(snapshot)

            if len(s3_buffer) >= BATCH_SIZE:  # 5 samples × 2s = 10s
                try:
                    batch_end_time = to_unix_timestamp(s3_buffer[-1]["timestamp"])
                    filename = f"{s3_prefix}{batch_start_time}_to_{batch_end_time}.json"

                    # TODO: enable this when data upload is needed
                    # s3.put_object(
                    #     Bucket=s3_bucket_name,
                    #     Key=filename,
                    #     Body=json.dumps(s3_buffer).encode("utf-8"),
                    #     ContentType="application/json"
                    # )

                    # Summarize in MongoDB
                    summary_doc = summarize_batch(
                        buffer=s3_buffer,
                        s3_path=filename,
                        start_time=batch_start_time,
                        end_time=batch_end_time
                    )

                    # print(summary_doc)
                    # mongo_collection.insert_one(summary_doc)

                    print(f"Uploaded {filename} with {len(s3_buffer)} entries")
                    
                    s3_buffer = []
                    batch_start_time = None
                
                except (BotoCoreError, NoCredentialsError) as e:
                    print(f"S3 upload error: {e}")
    except asyncio.CancelledError:
        print("[BackgroundCollector] Cancelled. Cleaning up...")
        raise
    except Exception as e:
        print(f"[BackgroundCollector] Error: {e}")
        raise

@app.on_event("shutdown")
async def stop_background_task():
    global background_task
    if background_task:
        print("[Shutdown] Cancelling background collector...")
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            print("[Shutdown] Background collector stopped.")