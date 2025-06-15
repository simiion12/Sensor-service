from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import datetime, timedelta

from app.database import get_db
from app.models import SensorData, Device
from app.schemas.sensors_schemas import SensorDataCreate, SensorData as SensorDataSchema, DeviceStatistics

router = APIRouter(prefix="/sensors", tags=["sensors"])


def get_water_status(level: float) -> str:
    if level >= 80:
        return "perfect"
    elif level >= 50:
        return "good"
    elif level >= 20:
        return "low"
    else:
        return "critical"


def get_beans_status(level: float) -> str:
    print(level)
    if level >= 80:
        return "perfect"
    elif level >= 50:
        return "good"
    elif level >= 20:
        return "low"
    else:
        return "critical"


def get_cups_status(coffee_count: int) -> str:
    if coffee_count == 4:
        return "perfect"
    elif coffee_count == 3:
        return "perfect"
    elif coffee_count == 2:
        return "good"
    elif coffee_count == 1:
        return "low"
    else:
        return "critical"


def get_cleaning_status(last_cleaning: datetime) -> str:
    days_since_cleaning = (datetime.utcnow() - last_cleaning).days

    if days_since_cleaning <= 1:
        return "perfect"
    elif days_since_cleaning <= 15:
        return "good"
    elif days_since_cleaning <= 30:
        return "low"
    else:
        return "critical"


@router.post("/", response_model=SensorDataSchema)
async def create_sensor_data(sensor_data: SensorDataCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Device).where(Device.id == sensor_data.device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db_sensor_data = SensorData(
        device_id=sensor_data.device_id,
        water_level=sensor_data.water_level,
        beans_level=sensor_data.beans_level,
        numbers_of_coffee=sensor_data.numbers_of_coffee
    )
    db.add(db_sensor_data)
    await db.commit()
    await db.refresh(db_sensor_data)
    return db_sensor_data


@router.get("/", response_model=List[SensorDataSchema])
async def get_sensor_data(db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(SensorData).offset(skip).limit(limit).order_by(SensorData.timestamp.desc())
    )
    sensor_data = result.scalars().all()
    return sensor_data


@router.get("/{id}", response_model=SensorDataSchema)
async def get_sensor_data_by_id(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SensorData).where(SensorData.id == id)
    )
    db_sensor_data = result.scalar_one_or_none()

    if db_sensor_data is None:
        raise HTTPException(status_code=404, detail="Sensor data not found")
    return db_sensor_data


@router.get("/device/{device_id}", response_model=List[SensorDataSchema])
async def get_sensor_data_by_device(device_id: int, db: AsyncSession = Depends(get_db), limit: int = 100):
    result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(limit)
    )
    sensor_data = result.scalars().all()
    return sensor_data

@router.get("/water/{device_id}")
async def get_water_status_endpoint(device_id: int = 1, db: AsyncSession = Depends(get_db)):
    device_result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    sensor_result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    latest_sensor_data = sensor_result.scalar_one_or_none()

    if not latest_sensor_data:
        return {"status": "perfect"}

    return {"status": latest_sensor_data.water_level or 100}


@router.get("/beans/{device_id}")
async def get_beans_status_endpoint(device_id: int = 1, db: AsyncSession = Depends(get_db)):
    device_result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    sensor_result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    latest_sensor_data = sensor_result.scalar_one_or_none()

    if not latest_sensor_data:
        return {"status": "perfect"}

    return {"status": latest_sensor_data.beans_level}


@router.get("/cleaning/{device_id}")
async def get_cleaning_status_endpoint(device_id: int = 1, db: AsyncSession = Depends(get_db)):
    device_result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return {"status": device.last_cleaning_time}


@router.get("/cups/{device_id}")
async def get_cups_status_endpoint(device_id: int = 1, db: AsyncSession = Depends(get_db)):
    device_result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return {"status": device.numbers_of_coffee or 0}

@router.get("/statistics/{device_id}", response_model=DeviceStatistics)
async def get_device_statistics(device_id: int = 1, db: AsyncSession = Depends(get_db)):
    device_result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    sensor_result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    latest_sensor_data = sensor_result.scalar_one_or_none()
    print(latest_sensor_data, "SENORDATA")

    if not latest_sensor_data:
        return {
            "name": device.device_name or "Magnifica-S",
            "statuses": {
                "water": {"status": "perfect"},
                "beans": {"status": "perfect"},
                "cleaning": {"status": "perfect"},
                "cups": {"status": "perfect"}
            }
        }

    water_status = get_water_status(latest_sensor_data.water_level or 100)
    beans_status = get_beans_status(latest_sensor_data.beans_level)
    cups_status = get_cups_status(device.numbers_of_coffee or 0)
    cleaning_status = get_cleaning_status(device.last_cleaning_time)

    return {
        "name": device.device_name or "Magnifica-S",
        "statuses": {
            "water": {"status": water_status},
            "beans": {"status": beans_status},
            "cleaning": {"status": cleaning_status},
            "cups": {"status": cups_status}
        }
    }


@router.delete("/{id}")
async def delete_sensor_data(sensor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SensorData).where(SensorData.id == sensor_id)
    )
    db_sensor_data = result.scalar_one_or_none()

    if db_sensor_data is None:
        raise HTTPException(status_code=404, detail="Sensor data not found")

    await db.delete(db_sensor_data)
    await db.commit()
    return {"message": f"Sensor data with id: {sensor_id}, deleted"}