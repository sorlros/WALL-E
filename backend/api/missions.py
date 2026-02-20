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

from api.auth import get_current_user

# ...

@router.post("/", response_model=schemas.Mission)
def create_mission(
    mission: schemas.MissionCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Ensure Profile exists for valid FK
    # (In a real app, this should be handled by Supabase triggers on auth.users insert,
    #  but for robustness we lazy-create it here if missing)
    profile = db.query(models.Profile).filter(models.Profile.id == current_user.id).first()
    if not profile:
        profile = models.Profile(
            id=current_user.id,
            username=current_user.email.split("@")[0] if current_user.email else "user",
            full_name=current_user.user_metadata.get("full_name") if current_user.user_metadata else None,
            # avatar_url...
        )
        db.add(profile)
        db.commit()
    
    # Create Mission in DB
    db_mission = models.Mission(
        user_id=current_user.id,
        title=mission.name, 
        description=mission.description,
        location_name=mission.location_name,
        location_address=mission.location_address,
        gps_lat=mission.gps_lat,
        gps_lng=mission.gps_lng
    )
    db.add(db_mission)
    db.commit()
    db.refresh(db_mission)
    
    # Set Active Mission in StreamManager
    if stream_manager_instance:
        stream_manager_instance.start_mission(db_mission.id)
            
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
    
    # Stop auto-saving AND stop the stream manager
    if stream_manager_instance:
        print(f"DEBUG: complete_mission called for {mission_id}. Active ID: {stream_manager_instance.active_mission_id}")
        
        if stream_manager_instance.active_mission_id == mission_id:
            stream_manager_instance.stop_mission()
        
        # Explicitly stop the stream/inference when mission completes
        if stream_manager_instance.is_running:
            print("DEBUG: Stopping StreamManager from complete_mission...")
            stream_manager_instance.release()
        else:
            print("DEBUG: StreamManager was not running.")
    else:
        print("DEBUG: stream_manager_instance is None!")
        
    return mission

@router.get("/", response_model=List[schemas.Mission])
def read_missions(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    missions = db.query(models.Mission).filter(models.Mission.user_id == current_user.id).offset(skip).limit(limit).all()
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
        bbox=bbox_data
        # GPS removed from here
    )
    
    
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)
    
    return db_detection

@router.patch("/detections/{detection_id}/gps", response_model=schemas.Mission)
def update_detection_gps(
    detection_id: int,
    gps_lat: float = Form(...),
    gps_lng: float = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Find detection to get mission_id
    detection = db.query(models.Detection).filter(models.Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
        
    # 2. Update MISSION's GPS (as per user request)
    mission = detection.mission
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found for this detection")
        
    mission.gps_lat = gps_lat
    mission.gps_lng = gps_lng
    
    db.commit()
    db.refresh(mission)
    return mission


