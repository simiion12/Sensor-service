import asyncio
import json
from datetime import datetime
import logging
from aiomqtt import Client, MqttError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import AsyncSessionLocal
from app.models import SensorData, Device

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self):
        self.client = None
        self.task = None
        self.is_connected = False
        self.latest_sensor_data = {}
        self.historical_data = []
        self.max_history_size = 100

    async def connect(self):
        try:
            self.client = Client(
                hostname=settings.mqtt_broker_host,
                port=settings.mqtt_broker_port
            )
            await self.client.__aenter__()
            self.is_connected = True
            logger.info(f"Connected to MQTT broker at {settings.mqtt_broker_host}:{settings.mqtt_broker_port}")

            await self.client.subscribe("coffee_machine/#")
            logger.info(f"Subscribed to topic: coffee_machine/#")

            self.task = asyncio.create_task(self.listen_for_messages())

        except MqttError as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            self.is_connected = False

    async def disconnect(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        if self.is_connected and self.client:
            await self.client.__aexit__(None, None, None)
            self.is_connected = False
            logger.info("Disconnected from MQTT broker")

    async def send_command(self, command):
        if not self.is_connected:
            raise ValueError("MQTT client is not connected")

        try:
            # Check if device is powered on for coffee/cleaning commands
            if command.get("action") in ["single_brew", "double_brew", "cleaning"]:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(Device).where(Device.id == 1)
                    )
                    device = result.scalar_one_or_none()

                    if device:
                        if not device.is_powered_on:
                            logger.warning(f"Device is powered off. Cannot execute {command.get('action')}")
                            return {"error": "device_powered_off"}

                        # Check coffee limit for brew commands
                        if command.get("action") in ["single_brew", "double_brew"]:
                            required_coffee = 1 if command.get("action") == "single_brew" else 2
                            if device.numbers_of_coffee < required_coffee:
                                logger.warning(
                                    f"Coffee limit exceeded. Available: {device.numbers_of_coffee}, Required: {required_coffee}")
                                return {"error": "daily_coffee_limit_exceeded", "available": device.numbers_of_coffee}

            # Handle power toggle separately - update database
            if command.get("action") == "power_toggle":
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(Device).where(Device.id == 1)
                    )
                    device = result.scalar_one_or_none()

                    if device:
                        device.is_powered_on = not device.is_powered_on
                        await db.commit()
                        logger.info(f"Device power toggled to: {'ON' if device.is_powered_on else 'OFF'}")

            command_json = json.dumps(command)
            logger.info(f"Sending command: {command_json}")

            await self.client.publish(
                topic="coffee_machine/commands",
                payload=command_json
            )
            return True
        except Exception as e:
            logger.error(f"Error sending command: {e}", exc_info=True)
            return False

    async def save_sensor_data_to_db(self, sensor_data):
        try:
            async with AsyncSessionLocal() as db:
                device_id = sensor_data.get('device_id', 1)
                water_level = sensor_data.get('water_level')
                beans_level = sensor_data.get('beans_level')
                action = sensor_data.get('action')
                status = sensor_data.get('status')

                if water_level is None and 'water_level' in sensor_data and isinstance(sensor_data['water_level'],
                                                                                       dict):
                    water_level = sensor_data['water_level'].get('percentage', 0)

                result = await db.execute(
                    select(Device).where(Device.id == device_id)
                )
                device = result.scalar_one_or_none()

                if not device:
                    logger.warning(f"Device with ID {device_id} not found")
                    return

                if action == "cleaning_completed":
                    from datetime import datetime
                    device.last_cleaning_time = datetime.utcnow()
                    await db.commit()
                    logger.info(f"Updated last cleaning time for device {device_id}")

                if status and "completed" in status:
                    if "single_brew_completed" in status:
                        device.numbers_of_coffee = max(0, device.numbers_of_coffee - 1)
                        await db.commit()
                        logger.info(f"Decremented coffee count for device {device_id}: {device.numbers_of_coffee}")
                    elif "double_brew_completed" in status:
                        device.numbers_of_coffee = max(0, device.numbers_of_coffee - 2)
                        await db.commit()
                        logger.info(f"Decremented coffee count for device {device_id}: {device.numbers_of_coffee}")

                if any([water_level is not None, beans_level is not None]):
                    db_sensor_data = SensorData(
                        device_id=device_id,
                        water_level=float(water_level) if water_level is not None else None,
                        beans_level=float(beans_level) if beans_level is not None else None
                    )

                    db.add(db_sensor_data)
                    await db.commit()
                    await db.refresh(db_sensor_data)

                    logger.info(f"Saved sensor data to database: ID {db_sensor_data.id}")
                    return db_sensor_data

        except Exception as e:
            logger.error(f"Error saving sensor data to database: {e}", exc_info=True)

    async def listen_for_messages(self):
        try:
            async for message in self.client.messages:
                try:
                    topic = message.topic.value
                    if isinstance(topic, bytes):
                        topic = topic.decode()
                    elif not isinstance(topic, str):
                        topic = str(topic)

                    payload = message.payload
                    if isinstance(payload, bytes):
                        payload_str = payload.decode()
                    else:
                        payload_str = str(payload)

                    payload_data = json.loads(payload_str)
                    timestamp = datetime.now()

                    if topic == "coffee_machine/sensor_data":
                        self.latest_sensor_data = {
                            "timestamp": timestamp,
                            "data": payload_data
                        }

                        self.historical_data.append({
                            "timestamp": timestamp,
                            "data": payload_data
                        })

                        if len(self.historical_data) > self.max_history_size:
                            self.historical_data.pop(0)

                        # Handle power toggle messages received from ESP32
                        if payload_data.get("action") == "power_toggle":
                            async with AsyncSessionLocal() as db:
                                result = await db.execute(
                                    select(Device).where(Device.id == 1)
                                )
                                device = result.scalar_one_or_none()

                                if device:
                                    # Use the power_state from the ESP32 message
                                    power_state = payload_data.get("power_state")
                                    if power_state is not None:
                                        device.is_powered_on = power_state
                                        await db.commit()
                                        logger.info(
                                            f"Device power updated from ESP32 to: {'ON' if device.is_powered_on else 'OFF'}")

                        await self.save_sensor_data_to_db(payload_data)

                    logger.info(f"Received message on topic {topic}: {payload_str}")

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse message payload as JSON: {message.payload}")
                except Exception as e:
                    logger.error(f"Error processing MQTT message: {e}", exc_info=True)

        except MqttError as e:
            logger.error(f"MQTT connection error: {e}")
            await asyncio.sleep(5)
            await self.connect()
        except Exception as e:
            logger.error(f"Unexpected error in MQTT listener: {e}", exc_info=True)


mqtt_client = MQTTClient()