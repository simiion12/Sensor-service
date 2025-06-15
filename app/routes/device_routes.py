from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Device, User
from app.schemas.device_schemas import DeviceCreate, Device as DeviceSchema

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/", response_model=DeviceSchema)
async def create_device(device: DeviceCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.id == device.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_device = Device(
        device_name=device.device_name,
        user_id=device.user_id,
        total_active_time=device.total_active_time
    )
    db.add(db_device)
    await db.commit()
    await db.refresh(db_device)
    return db_device


@router.get("/", response_model=List[DeviceSchema])
async def get_devices(db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(Device).offset(skip).limit(limit)
    )
    devices = result.scalars().all()
    return devices


@router.get("/{id}", response_model=DeviceSchema)
async def get_device(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Device).where(Device.id == id)
    )
    db_device = result.scalar_one_or_none()

    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return db_device


@router.put("/{id}", response_model=DeviceSchema)
async def update_device(device_id: int, device: DeviceCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    db_device = result.scalar_one_or_none()

    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    result = await db.execute(
        select(User).where(User.id == device.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_device.device_name = device.device_name
    db_device.user_id = device.user_id
    db_device.total_active_time = device.total_active_time

    await db.commit()
    await db.refresh(db_device)
    return db_device


@router.delete("/{id}")
async def delete_device(device_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    db_device = result.scalar_one_or_none()

    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    await db.delete(db_device)
    await db.commit()
    return {"message": f"Device with id: {device_id}, deleted"}