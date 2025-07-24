from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import random

# Router
voltage_router = APIRouter()

# In-memory voltage state
chassis_voltage_state = {}

CHASSIS_IDS = ["Chassis-1", "Chassis-2", "Chassis-3"]

def init_voltage_state(chassis_id: str):
    if chassis_id not in chassis_voltage_state:
        chassis_voltage_state[chassis_id] = [
            {"Name": "12V Rail", "ReadingVolts": round(random.uniform(11.8, 12.2), 2),
             "UpperThresholdCritical": 12.5, "LowerThresholdCritical": 11.5},
            {"Name": "5V Rail", "ReadingVolts": round(random.uniform(4.9, 5.1), 2),
             "UpperThresholdCritical": 5.25, "LowerThresholdCritical": 4.75},
            {"Name": "3.3V Rail", "ReadingVolts": round(random.uniform(3.2, 3.3), 2),
             "UpperThresholdCritical": 3.5, "LowerThresholdCritical": 3.0}
        ]

@voltage_router.get("/redfish/v1/Chassis/{chassis_id}/Power/Voltages")
def get_voltages(chassis_id: str):
    if chassis_id not in CHASSIS_IDS:
        raise HTTPException(status_code=404, detail="Chassis not found")
    init_voltage_state(chassis_id)
    return {"Voltages": chassis_voltage_state[chassis_id]}

@voltage_router.post("/redfish/v1/Chassis/{chassis_id}/Power/Voltages/Actions/Voltage.SetThresholds")
def set_voltage_thresholds(chassis_id: str, data: dict):
    """
    Expected input:
    {"Name": "12V Rail", "UpperThresholdCritical": 12.6, "LowerThresholdCritical": 11.4}
    """
    if chassis_id not in CHASSIS_IDS:
        raise HTTPException(status_code=404, detail="Chassis not found")
    init_voltage_state(chassis_id)

    name = data.get("Name")
    found = False
    for rail in chassis_voltage_state[chassis_id]:
        if rail["Name"] == name:
            found = True
            if "UpperThresholdCritical" in data:
                rail["UpperThresholdCritical"] = data["UpperThresholdCritical"]
            if "LowerThresholdCritical" in data:
                rail["LowerThresholdCritical"] = data["LowerThresholdCritical"]
    if not found:
        raise HTTPException(status_code=404, detail=f"Voltage rail '{name}' not found")
    return {"message": f"Thresholds updated for {name}"}
