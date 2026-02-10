from fastapi import FastAPI
from backend.api import stream
from backend.core.stream_manager import StreamManager
import asyncio

app = FastAPI(title="Wall-E Backend", version="0.1.0")

# Include routers
app.include_router(stream.router, prefix="/stream", tags=["stream"])

@app.get("/")
def read_root():
    return {"message": "Wall-E Backend is running"}

@app.on_event("startup")
async def startup_event():
    print("Starting up Wall-E backend...")

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down Wall-E backend...")
    # Clean up resources if needed
