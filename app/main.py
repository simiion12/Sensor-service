import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional, Any

from .mqtt_client import mqtt_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Coffee Machine Sensor Service")


class CommandRequest(BaseModel):
    action: str
    parameters: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    mqtt_status = "connected" if mqtt_client.is_connected else "disconnected"
    return {
        "status": "healthy",
        "mqtt": mqtt_status
    }


@app.get("/sensors/latest")
async def get_latest_sensor_data():
    """Get the most recent sensor readings."""
    if not mqtt_client.latest_sensor_data:
        raise HTTPException(status_code=404, detail="No sensor data available yet")

    return mqtt_client.latest_sensor_data


@app.get("/sensors/history")
async def get_sensor_history(limit: int = 10):
    """Get historical sensor data with optional limit."""
    if not mqtt_client.historical_data:
        raise HTTPException(status_code=404, detail="No historical data available")

    # Return the most recent entries based on the limit
    limit = min(limit, len(mqtt_client.historical_data))
    return mqtt_client.historical_data[-limit:]


@app.post("/coffee/brew")
async def brew_coffee():
    """Send a command to brew coffee."""
    if not mqtt_client.is_connected:
        raise HTTPException(status_code=503, detail="MQTT client is not connected")

    command = {
        "action": "brew_coffee"
    }

    success = await mqtt_client.send_command(command)
    if success:
        return {"status": "success", "message": "Brew command sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send brew command")


@app.post("/coffee/read_sensors")
async def request_sensor_reading():
    """Request an immediate sensor reading."""
    if not mqtt_client.is_connected:
        raise HTTPException(status_code=503, detail="MQTT client is not connected")

    command = {
        "action": "read_sensors"
    }

    success = await mqtt_client.send_command(command)
    if success:
        return {"status": "success", "message": "Sensor reading requested"}
    else:
        raise HTTPException(status_code=500, detail="Failed to request sensor reading")


@app.post("/command")
async def send_command(command: CommandRequest):
    """Send a custom command to the coffee machine."""
    if not mqtt_client.is_connected:
        raise HTTPException(status_code=503, detail="MQTT client is not connected")

    command_data = {
        "action": command.action
    }

    if command.parameters:
        command_data.update(command.parameters)

    success = await mqtt_client.send_command(command_data)
    if success:
        return {"status": "success", "message": f"Command '{command.action}' sent"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to send command '{command.action}'")

@app.get("/debug")
async def debug_info():
    """Get debug information about MQTT client and messages."""
    return {
        "mqtt_connected": mqtt_client.is_connected,
        "latest_data": mqtt_client.latest_sensor_data,
        "historical_count": len(mqtt_client.historical_data),
        "sample_history": mqtt_client.historical_data[-3:] if mqtt_client.historical_data else []
    }

@app.on_event("startup")
async def startup_event():
    """Connect to MQTT broker when the application starts."""
    logger.info("Starting up Coffee Machine Sensor Service...")
    await mqtt_client.connect()


@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect from MQTT broker when the application shuts down."""
    logger.info("Shutting down Coffee Machine Sensor Service...")
    await mqtt_client.disconnect()
