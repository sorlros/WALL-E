from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    missions = relationship("Mission", back_populates="user")

class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    description = Column(Text) # Hint text
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="missions")
    detections = relationship("Detection", back_populates="mission")

class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    image_path = Column(String)
    label = Column(String)
    confidence = Column(Float)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    address = Column(String, nullable=True) # "Suwon-si Gwonseon-dong"
    created_at = Column(DateTime, default=datetime.utcnow)

    mission = relationship("Mission", back_populates="detections")
