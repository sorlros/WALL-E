from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api import stream, missions, auth
import os

# Create storage directory if it doesn't exist
os.makedirs("storage", exist_ok=True)

app = FastAPI(title="Wall-E Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# Include routers
app.include_router(auth.router)
app.include_router(stream.router, prefix="/stream", tags=["stream"])
app.include_router(missions.router)

@app.get("/")
def read_root():
    return {"message": "Wall-E Backend is running"}

@app.on_event("startup")
async def startup_event():
    print("Starting up Wall-E backend...")
    # Inject stream_manager instance into missions API
    missions.set_stream_manager(stream.stream_manager)
    
    # Inject Main Event Loop into Stream API for Thread-Safe WebSocket Broadcast
    import asyncio
    stream.set_global_loop(asyncio.get_running_loop())

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down Wall-E backend...")
    # Clean up resources
    if stream.stream_manager:
        stream.stream_manager.release()
