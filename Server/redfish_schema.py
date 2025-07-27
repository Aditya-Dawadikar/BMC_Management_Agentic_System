from pydantic import BaseModel, Field
from typing import Dict, Optional, Union, Literal

# Define individual action data schemas
class FanActionData(BaseModel):
    fans: Dict[str, int] = Field(..., description="Fan speeds, e.g., {'Fan1': 50, 'Fan2': 60}")

class VoltageActionData(BaseModel):
    Name: str = Field(..., description="Voltage rail name, e.g., '12V Rail'")
    Upper: float = Field(..., description="UpperThresholdCritical")
    Lower: float = Field(..., description="LowerThresholdCritical")

class PowerActionData(BaseModel):
    Limit: int = Field(..., description="Power limit in Watts")

# Main Action schema
class RedfishAction(BaseModel):
    action_summary: str
    type: Literal["fan", "voltage", "power"]
    data: Union[FanActionData, VoltageActionData, PowerActionData]
    chassis_id: Optional[str] = Field("Chassis-1", description="Target chassis ID")
