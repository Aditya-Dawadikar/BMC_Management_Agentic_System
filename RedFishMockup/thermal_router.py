from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import random

thermal_router = APIRouter()

# Predefined sensors and fans
SENSOR_NAMES = ["CPU Temp", "GPU Temp", "Memory Temp", "VRM Temp", "Ambient Temp"]
FAN_NAMES = ["Fan1", "Fan2", "Fan3"]
THERMAL_POLICIES = ["Performance", "Balanced", "PowerSaving"]

# In-memory chassis states
chassis_state = {}

# List of chassis IDs
CHASSIS_IDS = ["Chassis-1", "Chassis-2", "Chassis-3"]


def init_all_chassis():
    for cid in CHASSIS_IDS:
        init_chassis_state(cid)


def init_chassis_state(chassis_id: str):
    if chassis_id not in chassis_state:
        chassis_state[chassis_id] = {
            "fans": {fan: random.randint(30, 60) for fan in FAN_NAMES},
            "temperatures": [],
            "policy": "Balanced",
            "thresholds": {}
        }


def generate_temperatures(chassis_id: str):
    temperatures = []
    for idx, name in enumerate(SENSOR_NAMES):
        temp = {
            "CPU Temp": random.randint(30, 120),
            "GPU Temp": random.randint(30, 120),
            "Memory Temp": random.randint(30, 120),
            "VRM Temp": random.randint(30, 120),
            "Ambient Temp": random.randint(20, 100),
        }[name]

        thresholds = {
            "CPU Temp": (70, 85, 95),
            "GPU Temp": (80, 95, 105),
            "Memory Temp": (65, 75, 85),
            "VRM Temp": (75, 90, 100),
            "Ambient Temp": (40, 50, 60),
        }[name]

        temperatures.append({
            "@odata.id": f"/redfish/v1/Chassis/{chassis_id}/Thermal#/Temperatures/{idx}",
            "MemberId": str(idx),
            "Name": name,
            "SensorNumber": idx + 1,
            "ReadingCelsius": temp,
            "UpperThresholdNonCritical": thresholds[0],
            "UpperThresholdCritical": thresholds[1],
            "UpperThresholdFatal": thresholds[2],
            "LowerThresholdNonCritical": 10,
            "LowerThresholdCritical": 5,
            "Status": {
                "State": "Enabled",
                "Health": "OK" if temp < thresholds[1] else "Warning"
            }
        })
    chassis_state[chassis_id]["temperatures"] = temperatures


@thermal_router.get("/redfish/v1/Chassis")
def list_chassis():
    init_all_chassis()
    chassis_list = [
        {
            "@odata.id": f"/redfish/v1/Chassis/{cid}",
            "Id": cid,
            "Name": f"Chassis {cid}",
            "Manufacturer": "MockCorp",
            "Model": "MockServer 1000",
        }
        for cid in CHASSIS_IDS
    ]
    return {"Members": chassis_list, "Members@odata.count": len(chassis_list)}


@thermal_router.get("/redfish/v1/Chassis/{chassis_id}")
def get_chassis(chassis_id: str):
    if chassis_id not in CHASSIS_IDS:
        raise HTTPException(status_code=404, detail="Chassis not found")
    init_chassis_state(chassis_id)
    generate_temperatures(chassis_id)
    fans = chassis_state[chassis_id]["fans"]
    policy = chassis_state[chassis_id]["policy"]

    overall_health = "OK"
    for t in chassis_state[chassis_id]["temperatures"]:
        if t["ReadingCelsius"] >= t["UpperThresholdCritical"]:
            overall_health = "Warning"
            break
    if any(speed < 20 for speed in fans.values()):
        overall_health = "Warning"

    chassis_status = {
        "@odata.id": f"/redfish/v1/Chassis/{chassis_id}",
        "@odata.type": "#Chassis.v1_20_0.Chassis",
        "Id": chassis_id,
        "Name": f"Chassis {chassis_id}",
        "Status": {
            "State": "Enabled",
            "Health": overall_health
        },
        "IndicatorLED": "Off",
        "Manufacturer": "MockCorp",
        "Model": "MockServer 1000",
        "ThermalPolicy": policy,
        "Links": {
            "Thermal": {"@odata.id": f"/redfish/v1/Chassis/{chassis_id}/Thermal"},
            "Power": {"@odata.id": f"/redfish/v1/Chassis/{chassis_id}/Power"}
        }
    }
    return JSONResponse(content=chassis_status)


@thermal_router.get("/redfish/v1/Chassis/{chassis_id}/Thermal")
def get_thermal(chassis_id: str):
    if chassis_id not in CHASSIS_IDS:
        raise HTTPException(status_code=404, detail="Chassis not found")
    init_chassis_state(chassis_id)
    generate_temperatures(chassis_id)
    response = {
        "@odata.id": f"/redfish/v1/Chassis/{chassis_id}/Thermal",
        "@odata.type": "#Thermal.v1_6_0.Thermal",
        "Id": "Thermal",
        "Name": f"Thermal Information for {chassis_id}",
        "Temperatures": chassis_state[chassis_id]["temperatures"],
        "Fans": [
            {
                "MemberId": str(idx),
                "Name": fan,
                "Reading": speed,
                "Units": "Percent",
                "Status": {"State": "Enabled", "Health": "OK"}
            }
            for idx, (fan, speed) in enumerate(chassis_state[chassis_id]["fans"].items())
        ]
    }
    return JSONResponse(content=response)


@thermal_router.post("/redfish/v1/Chassis/{chassis_id}/Thermal/Fans")
def set_fan_speed(chassis_id: str, fan_data: dict):
    if chassis_id not in CHASSIS_IDS:
        raise HTTPException(status_code=404, detail="Chassis not found")
    init_chassis_state(chassis_id)
    fans = chassis_state[chassis_id]["fans"]

    for fan, speed in fan_data.items():
        if fan not in fans:
            raise HTTPException(status_code=404, detail=f"Fan '{fan}' not found")
        if not (0 <= speed <= 100):
            raise HTTPException(status_code=400, detail=f"Invalid speed for {fan}")
        fans[fan] = speed
    return {"message": "Fan speeds updated", "fans": fans}


@thermal_router.post("/redfish/v1/Chassis/{chassis_id}/Thermal/Actions/Thermal.SetPolicy")
def set_thermal_policy(chassis_id: str, data: dict):
    if chassis_id not in CHASSIS_IDS:
        raise HTTPException(status_code=404, detail="Chassis not found")
    init_chassis_state(chassis_id)
    policy = data.get("Policy")
    if policy not in THERMAL_POLICIES:
        raise HTTPException(status_code=400, detail=f"Invalid policy. Allowed: {THERMAL_POLICIES}")
    chassis_state[chassis_id]["policy"] = policy
    return {"message": f"Thermal policy set to {policy}"}


@thermal_router.post("/redfish/v1/Chassis/{chassis_id}/Thermal/Actions/Thermal.ResetThresholds")
def reset_thresholds(chassis_id: str):
    if chassis_id not in CHASSIS_IDS:
        raise HTTPException(status_code=404, detail="Chassis not found")
    init_chassis_state(chassis_id)
    chassis_state[chassis_id]["thresholds"].clear()
    return {"message": "Temperature thresholds reset to defaults"}
