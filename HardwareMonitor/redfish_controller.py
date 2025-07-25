import os
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

BASE_URL=os.getenv("REDFISH_BASE_URL","http://localhost:8001/redfish/v1")
MAX_WORKERS=int(os.getenv("MAX_WORKERS", "5"))

def get_chassis_list():
    try:
        resp = requests.get(f"{BASE_URL}/Chassis", timeout=2).json()
        return [chassis["Id"] for chassis in resp.get("Members", [])]
    except Exception as e:
        print(f"Error fetching chassis list: {e}")
        return []

def fetch_endpoint(url):
    """Generic function to fetch a URL with timeout and return JSON or error."""
    try:
        return requests.get(url, timeout=3).json()
    except Exception as e:
        return {"error": str(e), "endpoint": url}

def get_chassis_snapshot(chassis_id):
    """Fetch Thermal, Power, and Voltages in parallel for a given chassis."""
    urls = {
        "thermal": f"{BASE_URL}/Chassis/{chassis_id}/Thermal",
        "power": f"{BASE_URL}/Chassis/{chassis_id}/Power",
        "voltages": f"{BASE_URL}/Chassis/{chassis_id}/Power/Voltages",
    }

    results = {}
    # Thread pool for the 3 parallel calls
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_key = {executor.submit(fetch_endpoint, url): key for key, url in urls.items()}
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"error": f"Thread failure: {e}"}

    thermal_data = results.get("thermal", {})
    power_data = results.get("power", {})
    volt_data = results.get("voltages", {})

    return {
        "Id": chassis_id,
        "Thermal": {
            "Policy": thermal_data.get("ThermalPolicy", "Balanced"),
            "Fans": thermal_data.get("Fans", []),
            "Temperatures": thermal_data.get("Temperatures", [])
        },
        "Power": {
            "PowerConsumedWatts": power_data.get("PowerControl", [{}])[0].get("PowerConsumedWatts"),
            "PowerLimit": power_data.get("PowerControl", [{}])[0].get("PowerLimit", {}).get("LimitInWatts"),
            "PowerSupplies": power_data.get("PowerSupplies", [])
        },
        "Voltages": volt_data.get("Voltages", [])
    }

def get_snapshot():
    """Fetch snapshot for all chassis in parallel."""
    chassis_ids = get_chassis_list()
    snapshot = {
                    "Chassis": [],
                    "timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
            }

    if not chassis_ids:
        return snapshot

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(get_chassis_snapshot, cid): cid for cid in chassis_ids}
        for future in as_completed(futures):
            try:
                snapshot["Chassis"].append(future.result())
            except Exception as e:
                snapshot["Chassis"].append({"error": f"Failed to collect snapshot: {e}"})
    return snapshot
