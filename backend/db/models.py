from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from .database import Base

# Supabase manages users in auth.users, but we can have a public profiles table
# However, for simplicity and foreign key constraints, we might just store user_id as UUID without strict FK if profiles table doesn't exist yet.
# Or we assume a profiles table exists. Let's assume we link to auth.users via a profile table if we created one, or just store UUID.
# Given the prompt, let's create a Profile model that maps to public.profiles

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(Text, nullable=True)
    full_name = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationship
    missions = relationship("Mission", back_populates="user")

class Mission(Base):
    __tablename__ = "missions"

    id = Column(BigInteger, primary_key=True, index=True) # Supabase uses bigserial
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    location_name = Column(Text, nullable=True)
    location_address = Column(Text, nullable=True)
    
    # We remove 'status' as we only save completed missions or active sessions
    # But to track if a mission is 'live' or 'done', a status is still useful in API logic
    # The user said "remove status because we only save completed data". 
    # But if we stream data to DB *during* flight, we need a parent record.
    # Let's keep the model simple as requested: NO status column.
    
    captured_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # GPS Info (Moved from Detection)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)

    user = relationship("Profile", back_populates="missions")
    detections = relationship("Detection", back_populates="mission")

    @property
    def name(self):
        return self.title

    @name.setter
    def name(self, value):
        self.title = value

class Detection(Base):
    __tablename__ = "detections"

    id = Column(BigInteger, primary_key=True, index=True)
    mission_id = Column(BigInteger, ForeignKey("missions.id"))
    
    image_url = Column(Text) # Supabase Storage URL
    label = Column(Text)
    confidence = Column(Float)
    
    # Bounding Box: [x, y, w, h]
    bbox = Column(JSONB, nullable=True)
    
    # gps_lat, gps_lng removed (moved to Mission)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    mission = relationship("Mission", back_populates="detections")
