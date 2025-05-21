from datetime import datetime
from pydantic import BaseModel

class SensorDataBase(BaseModel):
    water_level: float
    beans_level: float
    numbers_of_coffee: int


class SensorDataCreate(SensorDataBase):
    device_id: int


class SensorDataResponse(SensorDataBase):
    id: int
    device_id: int
    timestamp: datetime

    class Config:
        orm_mode = True