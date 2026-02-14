from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
import uuid
import json
from datetime import datetime

from db import models, schemas
from db.database import get_db

router = APIRouter(prefix="/missions", tags=["missions"])

# Directory to save uploaded images (Fallback / Local Cache)
UPLOAD_DIR = "storage/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Global instance reference (to be set by main or singleton)
stream_manager_instance = None 

def set_stream_manager(instance):
    global stream_manager_instance
    stream_manager_instance = instance

@router.post("/", response_model=schemas.Mission)
def create_mission(mission: schemas.MissionCreate, db: Session = Depends(get_db)):
    # Create Mission in DB
    db_mission = models.Mission(
        title=mission.title, 
        description=mission.description,
        location_name=mission.location_name,
        location_address=mission.location_address
    )
    db.add(db_mission)
    db.commit()
    db.refresh(db_mission)
    
    # Set Active Mission in StreamManager
    if stream_manager_instance:
        stream_manager_instance.active_mission_id = db_mission.id
        if not stream_manager_instance.is_running:
            stream_manager_instance.start()
            
    return db_mission

@router.post("/{mission_id}/complete", response_model=schemas.Mission)
def complete_mission(mission_id: int, db: Session = Depends(get_db)):
    # With Supabase, we might want to update captured_at or similar
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    mission.captured_at = datetime.utcnow()
    # If we had status, we would update it here.
    
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
    gps_lat: Optional[float] = Form(None),
    gps_lng: Optional[float] = Form(None),
    bbox: Optional[str] = Form(None), # JSON string
    db: Session = Depends(get_db)
):
    # Check if mission exists
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Generate unique filename
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    
    # TODO: Upload to Supabase Storage here instead of local file
    # For now, we save locally and return local path as URL
    
    today = datetime.now().strftime("%Y-%m-%d")
    save_dir = os.path.join(UPLOAD_DIR, today)
    os.makedirs(save_dir, exist_ok=True)
    
    file_path = os.path.join(save_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Mock URL (In real Supabase, this would be a public URL)
    image_url = f"/storage/images/{today}/{filename}"
    
    # Parse bbox JSON
    bbox_data = None
    if bbox:
        try:
            bbox_data = json.loads(bbox)
        except:
            pass
            
    db_detection = models.Detection(
        mission_id=mission_id,
        image_url=image_url,
        label=label,
        confidence=confidence,
        gps_lat=gps_lat,
        gps_lng=gps_lng,
        bbox=bbox_data
    )
    
    
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)
    
    return db_detection


