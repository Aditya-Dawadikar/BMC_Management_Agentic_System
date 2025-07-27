import os
import requests
import httpx
import asyncio
from dotenv import load_dotenv
from pymongo import MongoClient
from redfish_schema import RedfishAction
from mongo_crud.mongo_crud import log_action
from log_manager import push_log
from datetime import datetime, timezone

load_dotenv()

BASE_URL=os.getenv("REDFISH_BASE_URL", "http://localhost:8001/redfish/v1")

def publish_logs(actor: str, endpoint:str, payload:any, response:any, method: str="POST", status: int=200):
    """
        Helper Function to Log data to SSE and MongoDB
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Push Logs to SSE
    push_log({
            "actor": actor,
            "endpoint": endpoint,
            "payload":payload,
            "response": response,
            "timestamp": timestamp,
            "method": method,
            "status": status
        })
    
    # Push logs to MongoDb
    log_action(
        actor=actor,
        endpoint=endpoint,
        payload=payload,
        response=response,
        timestamp=timestamp,
        method=method,
        status=status
    )

def set_fan_speeds(fan_speeds: dict, chassis_id: str):
    """
    Set fan speeds for a given chassis.
    fan_speeds: dict like {"Fan1": 20, "Fan2": 10}
    """
    url = f"{BASE_URL}/Chassis/{chassis_id}/Thermal/Fans"
    try:
        resp = requests.post(url, json=fan_speeds)
        resp.raise_for_status()
        
        # Log the action
        publish_logs(
            actor="agent",
            endpoint=url,
            payload=fan_speeds,
            response=resp.json(),
            method=resp.request.method,
            status=resp.status_code
        )
        return resp.json()
    except Exception as e:
        print(f"Error setting fan speeds: {e}")
        return None

def set_voltage_thresholds(rail_name: str, upper: float, lower: float, chassis_id: str):
    """
    Set voltage thresholds for a specific voltage rail.
    name: voltage rail name, e.g., "12V Rail"
    upper: UpperThresholdCritical
    lower: LowerThresholdCritical
    """
    url = f"{BASE_URL}/Chassis/{chassis_id}/Power/Voltages/Actions/Voltage.SetThresholds"
    payload = {
        "Name": rail_name,
        "UpperThresholdCritical": upper,
        "LowerThresholdCritical": lower
    }
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        
        # Log the action
        publish_logs(
            actor="agent",
            endpoint=url,
            payload=payload,
            response=resp.json()
        )
        return resp.json()
    except Exception as e:
        print(f"Error setting voltage thresholds: {e}")
        return None

def set_power_limit(limit_watts: int, chassis_id: str):
    """
    Set power limit for a given chassis.
    limit_watts: integer power limit in Watts (e.g., 450)
    """
    url = f"{BASE_URL}/Chassis/{chassis_id}/Power/Actions/Power.SetPowerLimit"
    payload = {"LimitInWatts": limit_watts}
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        
        # Log the action
        publish_logs(
            actor="agent",
            endpoint=url,
            payload=payload,
            response=resp.json()
        )
        return resp.json()
    except Exception as e:
        print(f"Error setting power limit: {e}")
        return None

def redfish_factory(action: RedfishAction):
    if action.type == "fan":
        res= set_fan_speeds(action.data.fans, chassis_id=action.chassis_id)
        res["action_summary"] = action.action_summary
        return res

    elif action.type == "voltage":
        res= set_voltage_thresholds(
            action.data.Name,
            action.data.Upper,
            action.data.Lower,
            chassis_id=action.chassis_id
        )
        res["action_summary"] = action.action_summary
        return res

    elif action.type == "power":
        res= set_power_limit(
            action.data.Limit,
            chassis_id=action.chassis_id
        )
        res["action_summary"] = action.action_summary
        return res

    else:
        raise ValueError(f"Unknown action type: {action.type}")

async def get_chassis_ids():
    """Fetch all chassis IDs from /Chassis."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/Chassis")
        resp.raise_for_status()
        return [c.get("Id") or c["@odata.id"].split("/")[-1] for c in resp.json().get("Members", [])]

async def get_chassis_details(chassis_id: str):
    """Fetch Thermal, Power, and Voltages for a single chassis in parallel."""
    async with httpx.AsyncClient() as client:
        thermal_url = f"{BASE_URL}/Chassis/{chassis_id}/Thermal"
        power_url = f"{BASE_URL}/Chassis/{chassis_id}/Power"
        volt_url = f"{BASE_URL}/Chassis/{chassis_id}/Power/Voltages"

        thermal_task = client.get(thermal_url)
        power_task = client.get(power_url)
        volt_task = client.get(volt_url)

        thermal_resp, power_resp, volt_resp = await asyncio.gather(
            thermal_task, power_task, volt_task
        )

        return {
            "Id": chassis_id,
            "Thermal": thermal_resp.json(),
            "Power": power_resp.json(),
            "Voltages": volt_resp.json()
        }

async def get_all_chassis_data():
    """Fetch data for all chassis and return a single aggregated object."""
    chassis_ids = await get_chassis_ids()
    tasks = [get_chassis_details(cid) for cid in chassis_ids]
    all_chassis = await asyncio.gather(*tasks)
    return {"Chassis": all_chassis}
