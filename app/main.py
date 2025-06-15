import logging
from fastapi import FastAPI
from app.mqtt_client import mqtt_client
from app.routes.user_routes import router as user_router
from app.routes.device_routes import router as device_router
from app.routes.sensors_routes import router as sensor_router
from app.routes.command_routes import router as command_router
from app.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Coffee Machine Sensor Service")

app.include_router(user_router, prefix="/api")
app.include_router(device_router, prefix="/api")
app.include_router(sensor_router, prefix="/api")
app.include_router(command_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Coffee Machine Sensor Service"}

@app.get("/health")
async def health_check():
    mqtt_status = "connected" if mqtt_client.is_connected else "disconnected"
    return {
        "status": "healthy",
        "mqtt": mqtt_status
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Coffee Machine Sensor Service...")
    await mqtt_client.connect()
    start_scheduler()
    logger.info("Daily coffee count reset scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Coffee Machine Sensor Service...")
    await mqtt_client.disconnect()