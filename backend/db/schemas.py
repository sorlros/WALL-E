from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from datetime import datetime
import uuid

# Base Schemas
class DetectionBase(BaseModel):
    label: str
    confidence: float
    image_url: str
    bbox: Optional[List[Any]] = None # [x, y, w, h]

class DetectionCreate(DetectionBase):
    pass

class Detection(DetectionBase):
    id: int
    mission_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None

class MissionCreate(MissionBase):
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None

class Mission(MissionBase):
    id: int
    user_id: Optional[uuid.UUID] = None
    captured_at: Optional[datetime] = None
    created_at: datetime
    
    detections: List[Detection] = []

    model_config = ConfigDict(from_attributes=True)
