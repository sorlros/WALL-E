from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
# from core.stream_manager import stream_manager
from core.stream_manager_ai_only import stream_manager
import json
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            logger.warning("Broadcast called but no active connections.")
            return

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                logger.info(f"📤 [WebSocket] Sent {message.get('label')} to client {id(connection)}")
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
                pass

manager = ConnectionManager()

# Global Loop Reference (set by main.py)
global_loop = None

def set_global_loop(loop):
    global global_loop
    global_loop = loop

# Callback function to bridge StreamManager -> WebSocket
def detection_callback(data):
    logger.info(f"Callback received data: {data.get('label')}")
    if global_loop and global_loop.is_running():
        asyncio.run_coroutine_threadsafe(manager.broadcast(data), global_loop)
    else:
        logger.warning("Global loop not running or not set!")
        # Fallback if loop not set (e.g. testing)
        try:
           loop = asyncio.get_event_loop()
           if loop.is_running():
                asyncio.run_coroutine_threadsafe(manager.broadcast(data), loop)
        except:
            pass

# Register callback
stream_manager.set_callback(detection_callback)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.info(f"New Client Connected. Active clients: {len(manager.active_connections)}")
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(manager.active_connections)}")
        if len(manager.active_connections) == 0:
            logger.info("No active connections. Stopping StreamManager...")
            stream_manager.release()

@router.get("/live")
async def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    # We can start the stream manager here if it's not already running
    if not stream_manager.is_running:
        stream_manager.start()
        
    return StreamingResponse(stream_manager.generate_frames(), 
                             media_type="multipart/x-mixed-replace; boundary=frame")
