from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import random

# Router
power_router = APIRouter()

# In-memory chassis power state
chassis_power_state = {}

CHASSIS_IDS = ["Chassis-1", "Chassis-2", "Chassis-3"]

def init_power_state(chassis_id: str):
    if chassis_id not in chassis_power_state:
        chassis_power_state[chassis_id] = {
            "power_draw": random.randint(100, 300),  # Current power usage (Watts)
            "power_limit": 400,                      # Default limit
            "supplies": [
                {"Name": "PSU1", "Status": "OK", "CapacityWatts": 500, "InputVoltage": 230},
                {"Name": "PSU2", "Status": "OK", "CapacityWatts": 500, "InputVoltage": 230},
            ]
        }

@power_router.get("/redfish/v1/Chassis/{chassis_id}/Power")
def get_power(chassis_id: str):
    if chassis_id not in CHASSIS_IDS:
        raise HTTPException(status_code=404, detail="Chassis not found")
    init_power_state(chassis_id)

    power = chassis_power_state[chassis_id]
    response = {
        "@odata.id": f"/redfish/v1/Chassis/{chassis_id}/Power",
        "@odata.type": "#Power.v1_6_0.Power",
        "Id": "Power",
        "Name": f"Power Information for {chassis_id}",
        "PowerControl": [{
            "MemberId": "0",
            "PowerConsumedWatts": power["power_draw"],
            "PowerLimit": {
                "LimitInWatts": power["power_limit"]
            },
            "Status": {"State": "Enabled", "Health": "OK"}
        }],
        "PowerSupplies": power["supplies"]
    }
    return JSONResponse(content=response)

@power_router.post("/redfish/v1/Chassis/{chassis_id}/Power/Actions/Power.SetPowerLimit")
def set_power_limit(chassis_id: str, data: dict):
    if chassis_id not in CHASSIS_IDS:
        raise HTTPException(status_code=404, detail="Chassis not found")
    init_power_state(chassis_id)

    limit = data.get("LimitInWatts")
    if not isinstance(limit, int) or limit < 50 or limit > 1000:
        raise HTTPException(status_code=400, detail="LimitInWatts must be between 50 and 1000")
    chassis_power_state[chassis_id]["power_limit"] = limit
    return {"message": f"Power limit set to {limit} Watts"}
