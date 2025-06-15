from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DeviceBase(BaseModel):
    device_name: str
    user_id: int
    total_active_time: Optional[float] = 0

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    total_active_time: Optional[float] = None
    is_powered_on: Optional[bool] = None

class Device(DeviceBase):
    id: int
    numbers_of_coffee: int
    is_powered_on: bool
    last_cleaning_time: datetime
    created_at: datetime
    last_active: datetime

    class Config:
        from_attributes = True