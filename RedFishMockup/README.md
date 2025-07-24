# RedFish Mockup Server

This is a mockup server which is to be used as a proxy.
it will expose the same endpoints as RedFish.

---

## Installation

```cmd
pip install -r reqruiements.txt
```

## Start Server
```cmd
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Test the server

`GET http://localhost:8001/ping`


---

## **Supported Features**

* **Chassis**

  * List all chassis (`GET /redfish/v1/Chassis`)
  * Get chassis by ID (`GET /redfish/v1/Chassis/{id}`)

* **Thermal**

  * Query temperature sensors and fans
  * Set fan speeds
  * Set thermal policy (Performance/Balanced/PowerSaving)
  * Reset temperature thresholds

* **Power**

  * Query power consumption and PSU details
  * Set power limit

* **Voltage**

  * Query voltage rails (12V, 5V, 3.3V)
  * Update voltage thresholds


---

## **Base URL**

```
http://localhost:8000/redfish/v1
```

---

## **1. Chassis**

### **List all chassis**

```
GET /Chassis
```

**Response Example:**

```json
{
  "Members": [
    {"@odata.id": "/redfish/v1/Chassis/Chassis-1", "Id": "Chassis-1", "Name": "Chassis Chassis-1"},
    {"@odata.id": "/redfish/v1/Chassis/Chassis-2", "Id": "Chassis-2", "Name": "Chassis Chassis-2"}
  ],
  "Members@odata.count": 2
}
```

### **Get chassis details**

```
GET /Chassis/{chassis_id}
```

* Includes overall health, thermal policy, and links to Thermal and Power resources.

---

## **2. Thermal**

### **Get thermal information**

```
GET /Chassis/{chassis_id}/Thermal
```

* Returns an array of temperature sensors and fan states.

### **Set fan speeds**

```
POST /Chassis/{chassis_id}/Thermal/Fans
```

**Body Example:**

```json
{"Fan1": 70, "Fan2": 50}
```

### **Set thermal policy**

```
POST /Chassis/{chassis_id}/Thermal/Actions/Thermal.SetPolicy
```

**Body Example:**

```json
{"Policy": "Performance"}
```

### **Reset temperature thresholds**

```
POST /Chassis/{chassis_id}/Thermal/Actions/Thermal.ResetThresholds
```

---

## **3. Power**

### **Get power information**

```
GET /Chassis/{chassis_id}/Power
```

* Includes current power consumption, PSU details, and configured power limit.

### **Set power limit**

```
POST /Chassis/{chassis_id}/Power/Actions/Power.SetPowerLimit
```

**Body Example:**

```json
{"LimitInWatts": 450}
```

---

## **4. Voltages**

### **Get voltage readings**

```
GET /Chassis/{chassis_id}/Power/Voltages
```

* Lists voltage rails (12V, 5V, 3.3V) with current readings and thresholds.

### **Set voltage thresholds**

```
POST /Chassis/{chassis_id}/Power/Voltages/Actions/Voltage.SetThresholds
```

**Body Example:**

```json
{
  "Name": "12V Rail",
  "UpperThresholdCritical": 12.6,
  "LowerThresholdCritical": 11.4
}
```

---

## **5. Example cURL Commands**

### Get thermal data

```bash
curl http://localhost:8000/redfish/v1/Chassis/Chassis-1/Thermal | jq
```

### Set fan speeds

```bash
curl -X POST http://localhost:8000/redfish/v1/Chassis/Chassis-1/Thermal/Fans \
  -H "Content-Type: application/json" \
  -d '{"Fan1": 80}'
```

### Get power data

```bash
curl http://localhost:8000/redfish/v1/Chassis/Chassis-1/Power | jq
```

### Set power limit

```bash
curl -X POST http://localhost:8000/redfish/v1/Chassis/Chassis-1/Power/Actions/Power.SetPowerLimit \
  -H "Content-Type: application/json" \
  -d '{"LimitInWatts": 450}'
```

### Get voltages

```bash
curl http://localhost:8000/redfish/v1/Chassis/Chassis-1/Power/Voltages | jq
```

### Set voltage thresholds

```bash
curl -X POST http://localhost:8000/redfish/v1/Chassis/Chassis-1/Power/Voltages/Actions/Voltage.SetThresholds \
  -H "Content-Type: application/json" \
  -d '{"Name": "12V Rail", "UpperThresholdCritical": 12.6}'
```

---

## **6. Current Features**

* Multi-chassis support (`Chassis-1`, `Chassis-2`, `Chassis-3`).
* Dynamic temperature, power, and voltage values.
* In-memory state for fan speeds, power limits, and voltage thresholds.
