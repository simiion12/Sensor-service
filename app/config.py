from pydantic import BaseModel
from typing import Optional
import os

class Settings(BaseModel):
    # MQTT Settings
    mqtt_broker_host: str = os.getenv("MQTT_BROKER_HOST", "mqtt")
    mqtt_broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    mqtt_topic: str = os.getenv("MQTT_TOPIC", "coffee_machine/#")

settings = Settings()