from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.api import stream, missions
import os

# Create storage directory if it doesn't exist
os.makedirs("backend/storage", exist_ok=True)

app = FastAPI(title="Wall-E Backend", version="0.1.0")

# Mount Static Files
app.mount("/storage", StaticFiles(directory="backend/storage"), name="storage")

# Include routers
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

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down Wall-E backend...")
    # Clean up resources if needed
