from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CrackCreate(BaseModel):
    """드론이 데이터를 보낼 때 사용하는 모델"""
    latitude: float
    longitude: float
    confidence: float
    image_url: Optional[str] = None  # 크랙 사진이 있다면 경로 저장

class CrackResponse(CrackCreate):
    """프론트엔드로 데이터를 내려줄 때 사용하는 모델"""
    id: int
    detected_at: datetime

    class Config:
        from_attributes = True