
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from core.stream_manager import stream_manager

router = APIRouter()

@router.get("/live")
async def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    # We can start the stream manager here if it's not already running
    if not stream_manager.is_running:
        stream_manager.start()
        
    return StreamingResponse(stream_manager.generate_frames(), 
                             media_type="multipart/x-mixed-replace; boundary=frame")
