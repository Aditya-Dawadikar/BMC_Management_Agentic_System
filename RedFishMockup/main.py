from fastapi import FastAPI
from fastapi.responses import JSONResponse
from power_router import power_router
from voltage_router import voltage_router
from thermal_router import thermal_router

app = FastAPI(title="Mock Redfish Server")

# Include routers
app.include_router(power_router)
app.include_router(voltage_router)
app.include_router(thermal_router)

@app.get("/ping")
def ping():
    response={
        "message": "success"
    }
    return JSONResponse(content=response)