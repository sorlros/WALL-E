from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DetectionBase(BaseModel):
    label: str
    confidence: float
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    address: Optional[str] = None

class DetectionCreate(DetectionBase):
    pass

class Detection(DetectionBase):
    id: int
    mission_id: int
    image_path: str
    created_at: datetime

    class Config:
        orm_mode = True

class MissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class MissionCreate(MissionBase):
    pass

class Mission(MissionBase):
    id: int
    user_id: Optional[int] = None # For now optional until auth is fully integrated
    status: str
    created_at: datetime
    detections: List[Detection] = []

    class Config:
        orm_mode = True
