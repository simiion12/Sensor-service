from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SensorDataBase(BaseModel):
    device_id: int
    water_level: Optional[float] = None
    beans_level: Optional[float] = None
    numbers_of_coffee: Optional[int] = 0

class SensorDataCreate(SensorDataBase):
    pass

class SensorData(SensorDataBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class DeviceStatus(BaseModel):
    status: str

class DeviceStatistics(BaseModel):
    name: str
    statuses: dict