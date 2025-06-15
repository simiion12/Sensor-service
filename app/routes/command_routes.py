from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from app.mqtt_client import mqtt_client

router = APIRouter(prefix="/commands", tags=["commands"])


class CommandRequest(BaseModel):
    action: str
    parameters: Optional[Dict[str, Any]] = None


@router.get("/sensors/latest")
async def get_latest_sensor_data():
    if not mqtt_client.latest_sensor_data:
        raise HTTPException(status_code=404, detail="No sensor data available yet")
    return mqtt_client.latest_sensor_data


@router.get("/sensors/history")
async def get_sensor_history(limit: int = 10):
    if not mqtt_client.historical_data:
        raise HTTPException(status_code=404, detail="No historical data available")
    limit = min(limit, len(mqtt_client.historical_data))
    return mqtt_client.historical_data[-limit:]


@router.post("/coffee/single_brew")
async def single_brew():
    if not mqtt_client.is_connected:
        raise HTTPException(status_code=503, detail="MQTT client is not connected")

    result = await mqtt_client.send_command({"action": "single_brew"})
    if result is True:
        return {"status": "success", "message": "Single brew command sent"}
    elif isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=f"Coffee limit exceeded. Available: {result['available']} coffees")
    else:
        raise HTTPException(status_code=500, detail="Failed to send single brew command")


@router.post("/coffee/double_brew")
async def double_brew():
    if not mqtt_client.is_connected:
        raise HTTPException(status_code=503, detail="MQTT client is not connected")

    result = await mqtt_client.send_command({"action": "double_brew"})
    if result is True:
        return {"status": "success", "message": "Double brew command sent"}
    elif isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=f"Coffee limit exceeded. Available: {result['available']} coffees")
    else:
        raise HTTPException(status_code=500, detail="Failed to send double brew command")


@router.post("/coffee/power_toggle")
async def power_toggle():
    if not mqtt_client.is_connected:
        raise HTTPException(status_code=503, detail="MQTT client is not connected")

    # Don't update database here, let ESP32 report the state change
    success = await mqtt_client.send_command({"action": "power_toggle"})
    if success:
        return {"status": "success", "message": "Power toggle command sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send power toggle command")


@router.post("/coffee/cleaning")
async def start_cleaning():
    if not mqtt_client.is_connected:
        raise HTTPException(status_code=503, detail="MQTT client is not connected")

    success = await mqtt_client.send_command({"action": "cleaning"})
    if success:
        return {"status": "success", "message": "Cleaning command sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send cleaning command")


@router.post("/coffee/read_sensors")
async def request_sensor_reading():
    if not mqtt_client.is_connected:
        raise HTTPException(status_code=503, detail="MQTT client is not connected")

    success = await mqtt_client.send_command({"action": "read_sensors"})
    if success:
        return {"status": "success", "message": "Sensor reading requested"}
    else:
        raise HTTPException(status_code=500, detail="Failed to request sensor reading")


@router.post("/send")
async def send_command(command: CommandRequest):
    if not mqtt_client.is_connected:
        raise HTTPException(status_code=503, detail="MQTT client is not connected")

    command_data = {"action": command.action}
    if command.parameters:
        command_data.update(command.parameters)

    success = await mqtt_client.send_command(command_data)
    if success:
        return {"status": "success", "message": f"Command '{command.action}' sent"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to send command '{command.action}'")


@router.get("/debug")
async def debug_info():
    return {
        "mqtt_connected": mqtt_client.is_connected,
        "latest_data": mqtt_client.latest_sensor_data,
        "historical_count": len(mqtt_client.historical_data),
        "sample_history": mqtt_client.historical_data[-3:] if mqtt_client.historical_data else []
    }