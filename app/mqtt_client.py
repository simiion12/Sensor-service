import asyncio
import json
from datetime import datetime
import logging
from aiomqtt import Client, MqttError
from .config import settings
from .models import SensorData

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self):
        self.client = None
        self.task = None
        self.is_connected = False
        # Store the most recent sensor data
        self.latest_sensor_data = {}
        # Store historical sensor data (limited to last 100 readings)
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

            # Subscribe to coffee machine topics
            await self.client.subscribe("coffee_machine/#")
            logger.info(f"Subscribed to topic: coffee_machine/#")

            # Start listening for messages
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
        """Send a command to the coffee machine"""
        if not self.is_connected:
            raise ValueError("MQTT client is not connected")

        try:
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

    async def listen_for_messages(self):
        try:
            async for message in self.client.messages:
                try:
                    # Safely convert topic from bytes to string
                    topic = message.topic.value
                    if isinstance(topic, bytes):
                        topic = topic.decode()
                    elif not isinstance(topic, str):
                        topic = str(topic)

                    # Safely convert payload from bytes to string
                    payload = message.payload
                    if isinstance(payload, bytes):
                        payload_str = payload.decode()
                    else:
                        payload_str = str(payload)

                    # Parse JSON payload
                    payload_data = json.loads(payload_str)

                    # Store the data with the topic as key
                    timestamp = datetime.now()

                    # Process and store sensor data
                    if topic == "coffee_machine/sensor_data":
                        # Store as latest data
                        self.latest_sensor_data = {
                            "timestamp": timestamp,
                            "data": payload_data
                        }

                        # Add to historical data
                        self.historical_data.append({
                            "timestamp": timestamp,
                            "data": payload_data
                        })

                        # Limit the size of historical data
                        if len(self.historical_data) > self.max_history_size:
                            self.historical_data.pop(0)

                    # Print to console for debugging
                    logger.info(f"Received message on topic {topic}: {payload_str}")

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse message payload as JSON: {message.payload}")
                except Exception as e:
                    logger.error(f"Error processing MQTT message: {e}", exc_info=True)

        except MqttError as e:
            logger.error(f"MQTT connection error: {e}")
            # Try to reconnect
            await asyncio.sleep(5)
            await self.connect()
        except Exception as e:
            logger.error(f"Unexpected error in MQTT listener: {e}", exc_info=True)

mqtt_client = MQTTClient()