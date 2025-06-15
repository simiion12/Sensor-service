from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)

    # Relationship with devices
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email})"


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_name = Column(String, nullable=False)
    total_active_time = Column(Float, default=0)
    last_cleaning_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    numbers_of_coffee = Column(Integer, default=4)
    is_powered_on = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="devices")
    sensor_data = relationship("SensorData", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Device(id={self.id}, name={self.device_name}, user_id={self.user_id})"


class SensorData(Base):
    __tablename__ = "sensors_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    water_level = Column(Float)
    beans_level = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship
    device = relationship("Device", back_populates="sensor_data")

    def __repr__(self):
        return f"SensorData(id={self.id}, device_id={self.device_id}, water_level={self.water_level}, beans_level={self.beans_level})"