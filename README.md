# Sensor Service

A FastAPI-based microservice that handles sensor data ingestion, storage, caching, and messaging through MQTT, Kafka, PostgreSQL (Neon), and Redis.

## 📁 Project Structure

````
sensor-service/
├── app/
│ ├── init.py
│ ├── main.py # FastAPI app with startup/shutdown events
│ ├── config.py # Pydantic settings for MQTT, Kafka, Neon, Redis
│ ├── mqtt_client.py # Async MQTT client
│ ├── kafka_producer.py # Async Kafka producer
│ ├── models.py # Pydantic schemas for sensor payloads
│ ├── db/
│ │ ├── session.py # Async SQLAlchemy session with Neon DB
│ │ └── crud.py # Basic INSERT and SELECT operations
│ ├── api/
│ │ ├── health.py # /health endpoint
│ │ ├── sensors.py # Endpoints for latest + historical sensor data
│ │ └── commands.py # Endpoint to POST sensor commands
│ └── cache.py # Redis helper for caching latest sensor data
├── alembic/ # Database migration scripts
├── tests/ # Unit tests for data parsing and DB logic
├── Dockerfile # Container image for FastAPI app
└── docker-compose.yml # Services: Mosquitto, Kafka, Zookeeper, Redis, Neon (or use remote Neon DB)
````

## 🚀 Features

- Async FastAPI app
- MQTT client for sensor data ingestion
- Kafka producer for stream processing
- PostgreSQL (Neon) for persistent storage
- Redis cache for real-time sensor data
- Health check and REST API endpoints
- Dockerized for local development and deployment

## 🐳 Running the Project

```bash
docker-compose up --build
