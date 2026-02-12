from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
import uuid
from datetime import datetime

from backend.db import models, schemas
from backend.db.database import get_db

router = APIRouter(prefix="/missions", tags=["missions"])

# Directory to save uploaded images
UPLOAD_DIR = "backend/storage/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

from backend.core.stream_manager import StreamManager

# ...

# We need access to the running StreamManager instance
# In a real app, this might be a singleton dependency injection
# For now, we import the instance if it's a global or managed in main
# But StreamManager is instantiated in main.py? 
# Actually, StreamManager is usually a singleton. 
# Let's assume we can import the instance from a shared module or main.
# To avoid circular imports with main, let's instantiate a global stream_manager in core.

from backend.core.stream_manager import StreamManager

# Global instance reference (to be set by main or singleton)
stream_manager_instance = None 

def set_stream_manager(instance):
    global stream_manager_instance
    stream_manager_instance = instance

@router.post("/", response_model=schemas.Mission)
def create_mission(mission: schemas.MissionCreate, db: Session = Depends(get_db)):
    # Create Mission in DB
    db_mission = models.Mission(name=mission.name, description=mission.description)
    db.add(db_mission)
    db.commit()
    db.refresh(db_mission)
    
    # Set Active Mission in StreamManager
    # This enables the auto-save logic
    if stream_manager_instance:
        stream_manager_instance.active_mission_id = db_mission.id
        # Also could enable stream if not running
        if not stream_manager_instance.is_running:
            stream_manager_instance.start()
            
    return db_mission

@router.post("/{mission_id}/complete", response_model=schemas.Mission)
def complete_mission(mission_id: int, db: Session = Depends(get_db)):
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    mission.status = "completed"
    db.commit()
    
    # Stop auto-saving
    if stream_manager_instance and stream_manager_instance.active_mission_id == mission_id:
        stream_manager_instance.active_mission_id = None
        
    return mission

@router.get("/", response_model=List[schemas.Mission])
def read_missions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    missions = db.query(models.Mission).offset(skip).limit(limit).all()
    return missions

@router.get("/{mission_id}", response_model=schemas.Mission)
def read_mission(mission_id: int, db: Session = Depends(get_db)):
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

@router.post("/{mission_id}/detections", response_model=schemas.Detection)
async def create_detection(
    mission_id: int,
    file: UploadFile = File(...),
    label: str = Form(...),
    confidence: float = Form(...),
    gps_lat: float = Form(None),
    gps_lng: float = Form(None),
    db: Session = Depends(get_db)
):
    # Check if mission exists
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Generate unique filename
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    
    # Organize by date to avoid huge directories
    today = datetime.now().strftime("%Y-%m-%d")
    save_dir = os.path.join(UPLOAD_DIR, today)
    os.makedirs(save_dir, exist_ok=True)
    
    file_path = os.path.join(save_dir, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create DB record
    # Store relative path for portability
    relative_path = os.path.join("storage/images", today, filename)
    
    db_detection = models.Detection(
        mission_id=mission_id,
        image_path=relative_path,
        label=label,
        confidence=confidence,
        gps_lat=gps_lat,
        gps_lng=gps_lng
    )
    
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)
    
    return db_detection
