# Wall-E AI Assistant Definition

This file provides the essential context and specialized instructions for the Antigravity AI agent to assist the Wall-E team effectively.

## 🛠 1. Project Global Context
**Project Name:** Wall-E

**Mission:** Real-time building exterior crack detection and GPS logging using drone RTMP streaming.

**Core Tech Stack:**
- **App:** Flutter (3.27.x), Dart (3.6.x)
- **Server:** FastAPI (0.115.0)
- **AI:** YOLOv8 (8.3.0), PyTorch (2.4.0), OpenCV (4.10.0.84)
- **Data Pipeline:** Drone -> RTMP Stream -> Backend (AI Inference) -> WebSocket -> Flutter App

## 🤖 2. Specialized Skill Definitions

### [Skill: Wall-E-Architect]
**Role:** Oversees system integration and structural integrity.

**Instructions:**
- Enforce the designated directory structure (`app/`, `backend/`, `models/`, `ai_research/`).
- Ensure consistent data schemas (JSON) across all communication layers.
- Strictly adhere to the library versions specified in the `README.md`.

### [Skill: Wall-E-AI-Inference]
**Role:** Real-time video processing and YOLOv8 model optimization.

**Instructions:**
- **Hardware Acceleration:** Always check for hardware availability: use `mps` for Apple Silicon (M1/M2/M3), `cuda` for NVIDIA GPUs, and `cpu` as a fallback.
- **Optimization:** Prioritize real-time performance using 640x640 Letterbox preprocessing and Frame-Skipping logic.
- **Inference Output:** Extract bounding box coordinates (xyxy) and confidence scores (conf) using the `ultralytics` framework.

### [Skill: Wall-E-Backend-Dev]
**Role:** FastAPI server management and real-time data streaming.

**Instructions:**
- **Asynchronous:** Use `async`/`await` as the default for all API endpoints and WebSocket handlers.
- **Stream Handling:** Implement efficient memory management for RTMP ingestion using OpenCV `VideoCapture`.
- **Logging:** Log critical events such as stream connection status and inference latency (ms) for debugging purposes.

### [Skill: Wall-E-Flutter-Dev]
**Role:** Mobile UI development and real-time visualization.

**Instructions:**
- **UI/UX:** Use the `video_player` package for RTMP feed and a `Stack` widget to overlay real-time bounding boxes.
- **Communication:** Implement `web_socket_channel` with robust error handling and auto-reconnect logic.

## 📏 3. Coding Standards & Guidelines
- **No Magic Numbers:** All constants (e.g., resolution 640, confidence threshold 0.5) must be stored in a `config.py` or as named constants.
- **Cross-Platform Pathing:** Use `pathlib` or `os.path.join` to ensure compatibility between macOS and Windows.
- **Documentation:** Every function and class must include a clear docstring describing its purpose and parameters.
- **Resilience:** Implement comprehensive `try-except` blocks to handle network instability and stream interruptions.
