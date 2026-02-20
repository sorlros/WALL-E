[🇺🇸 English](README.md) | [🇰🇷 한국어](README_KR.md)

# 🛸 Wall-E: Drone-Based Exterior Crack Detection System
> **Project Duration:** 2026.02.09 ~ 2026.02.25 (16 Days)

**Wall-E** is an automated inspection system that utilizes drone imagery to detect cracks and defects on building exteriors. Our solution leverages computer vision technology and a hyper-converged multi-threaded streaming architecture to identify, classify, and visualize structural anomalies, providing a safer and more efficient maintenance workflow.

---

## 🏗️ System Architecture

Video captured by the drone is streamed to the user's smartphone (Flutter app), while a backend video server acts as the intermediary, handling real-time AI analysis and duplicate filtering.

```mermaid
graph TD
    Drone["🚁 Drone (DJI Phantom 4 Pro)"]
    RTMP["📡 Media Server (MediaMTX)<br/>[RTMP 1935]"]
    Backend["💻 Backend Server (FastAPI/Python)<br/>[HTTP 8000]"]
    DB[("🐘 Database<br/>(Supabase PostgreSQL)")]
    App["📱 Client App (Flutter)<br/>[Android/iOS]"]

    Drone -- "1. Raw Live Stream<br/>(720p, 30fps)" --> RTMP
    RTMP -- "2. Video Stream Polling" --> Backend
    Backend -- "4. AI Inference & Results<br/>(Mission, Detections)" --> DB
    Backend -- "3. Mobile-Optimized Stream<br/>(MJPEG, 720p 30fps)" --> App
    App -- "5. API Requests (Manual Capture)" --> Backend
    App -- "6. Load Gallery Images" --> DB
```

---

## 👥 Team Structure & Roles

👉 **[View Project Kanban Board (GitHub Projects)](https://github.com/orgs/WallEproject/projects/1/views/1)**

| Role | Responsibilities | Key Focus Areas |
|------|------------------|-----------------|
| **Project Architecture (PA)** | System Architecture, Tech Direction, Documentation | 3-Track Async Architecture Design, System Integration |
| **Backend Developer** | Server Architecture, API, DB Design | FastAPI, Supabase, REST API, StreamManager Multi-threading |
| **AI Model Developer** | Model Training (YOLO), Re-ID Logic | Albumentations Augmentation, MobileNetV3 Embedding, Inference |
| **Frontend Developer** | Mobile App Development (Flutter) | Floating Action Button (FAB), MJPEG Live Stream View, State Management |

---

## 📅 Core Project Pipeline

### 1. 🧠 AI & Computer Vision Part
The core engine for real-time crack detection from drone footage and duplicate prevention.
*   **Object Detection**: YOLOv11n (Nano) - Ultra-fast real-time object recognition.
*   **Duplicate Filtering (Re-Identification)**: Powered by the `MobileNetV3-small` model.
    *   Prevents storing multiple images of the same crack caused by drone shaking.
    *   Crops the crack, converts it to a 576-dimensional embedding, and compares it with recent cache using **Cosine Similarity**. If it matches >= 80%, it is discarded (Dropped).
*   **Dataset Augmentation**:
    *   Uses `Albumentations` to perfectly simulate vertical flight shaking (Shift), Motion Blur, and backlight.
    *   Applies **Hard Negative Mining** by aggressively treating fake cracks (e.g., wires, tile joints) as Background files to drastically lower false positives.

### 2. ⚙️ Backend & Architecture Part
A Zero-Latency 3-Track Asynchronous Architecture that entirely eliminates thread bottlenecks.
*   **Thread 1 (Camera Reception)**: Fully dedicated to dumping the latest drone frames into memory, ignoring all encoding/AI operations to defend the buffer.
*   **Thread 2 (AI Inference)**: "Steals" the latest frame to run YOLO inference + update BBox + verify Re-ID filter + asynchronously save manual captures.
*   **Thread 3 (Mobile Streaming)**: Merges the clean photo from Thread 1 with the coordinates from Thread 2, resizes it to 720p 30FPS for optimization, and shoots it as MJPEG to the smartphone.
*   **Database & Storage**: Supabase (PostgreSQL) - Unifies Detection history, Auth, and Image Storage.

### 3. 📱 Frontend (App) Part
The interface for users to monitor zero-delay video and control drone inspections.
*   **Real-time Monitoring**: Utilizing `flutter_mjpeg` to hit 30FPS perfectly without black screens or memory leaks.
*   **Manual Capture**: Users can actively record hazards using a Floating Action Button (FAB) during live streaming, instantly saving to DB (`is_manual=true`) equipped with a dedicated visually distinctive badge.
*   **Gallery & Map Integration**: Google Maps screens check mission locations, reviewing results (BBox Box On/Off) dynamically.

---

## 🛠 Tech Stack

### Core
*   **Language**: Python 3.10+, Dart 3.3+
*   **AI**: YOLOv11 (`ultralytics`), PyTorch (`MobileNetV3`), OpenCV, Albumentations
*   **Backend**: FastAPI, SQLAlchemy, PostgreSQL (`psycopg2`)
*   **Frontend**: Flutter 3.19+

### Infrastructure
*   **DB/Auth/Storage**: Supabase (Cloud)
*   **Streaming Server**: MediaMTX (RTMP)
    *   **Stream Route**: `rtmp://<Server-IP>:1935/live/drone`

---

## 🌊 Getting Started

### 1. Environment Setup

#### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
> ※ Requires the AI offline weight models (`backend/models/mobile_net_v3_small.pth`).

#### Database (Supabase)
Configure Supabase connection info in the `.env` file.
```env
DATABASE_URL=postgresql://user:pass@host:6543/postgres
SUPABASE_URL=...
SUPABASE_KEY=...
RTMP_URL=rtmp://localhost:1935/live/drone
```

### 2. Execution

#### RTMP Media Server (MediaMTX)
* The `mediamtx` server is currently running on a **team member's Windows/Linux desktop**, not on this MacBook.
* **Port Forwarding** has been configured on port `1935` to allow the drone and the backend server to access the video feed externally.
* There is no need to manually start the media server on this local machine.

#### Backend Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start Frontend App
cd frontend
flutter run
```

---

## 🚀 Development Timeline

### 📍 2026.02.11 ~ 02.13 (Phase 1: Foundation & Base Infrastructure)
- **Unified DB/Auth Infrastructure**: Configured the initial Supabase PostgreSQL schema and deployed functional Login/Signup endpoints via FastAPI.
- **Real-Time Baseline**: Bootstrapped MediaMTX integrations, foundational OpenCV frame captures, and localized Bounding Box overlays.
- **Object Tracking Implementation**: Integrated YOLO's `model.track()` and an active ID cache `Set` to prevent multi-saves of static drone footage.
- **Core Flutter Scaffolding**: Structured the baseline App UI routes spanning across New Mission, Gallery, and Profile screens.

### 📍 2026.02.16 (Refactoring Day & UX Improvements)
- **Frontend Type Safety Assured**: Solidified API responses by introducing strict `Mission`, `Detection`, and `User` Dart models.
- **Zero-Delay & BBox Ratio Fix**: Removed pre-inference padding to precisely map bounding box coordinates over raw frames, eliminating y-axis displacement.
- **Gallery UI Upgrades**: Implemented PageView swipe navigation and responsive Landscape/Portrait bounds on the detail screen.
- **Backend Metadata Hierarchy Swap**: Optimized overall DB structural integrity by migrating GPS variables strictly from detections upwards to the missions table.

### 📍 2026.02.17 ~ 02.19 (Phase 2: Streaming Paradigm Shift & Data Security)
- **Google Maps Integration**: Shifted static map placeholders to the active Google Maps Static API for active mission locale and GPS coordinate tracking.
- **Data Isolation (RLS)**: Enforced strict Supabase Row Level Security protocols, ensuring users only access their personal flight registries.
- **Streaming Protocol Shift (HLS ➔ MJPEG)**: Physically bypassed HLS buffering latency (3-5s) and WebSocket Desync bugs by having the backend pre-burn coordinate boxes uniformly into MJPEG payloads.
- **OpenCV Backend Auto-Detection**: Dropped explicit `CAP_FFMPEG` allocations to guarantee stable Mac Apple Silicon and Server hardware-accelerated video encodings.
- **UX & Localization Bug Fixes**: Obliterated Korean UTF-8 encoding corruption bugs and formally solidified Android permission configurations.

### 📍 2026.02.20 (Phase 3: Real-Time Optimization & AI Enhancement)
- **3-Track Async Streaming Architecture**: Fully decoupled video reception, AI inference, and client broadcast, erasing Stuttering bottlenecks to realize Zero-Latency.
- **Mobile Streaming Optimization**: Resolved stuttering and black screens by importing `flutter_mjpeg` and enforcing 720p 30FPS server-side resizing.
- **MobileNetV3 Deduplication (Re-ID)**: Mitigated multi-save tracking limitation scenarios caused by drone wobble using embedding Cosine Similarity (80% Threshold / 10% Margin).
- **Manual Capture Integration**: Granted users unilateral snapshot power via a live frontend FAB, tagging them in DB as explicit "Manual Captures".
- **Augmentation Pipeline Plan**: Drafted robust data strategies detailing vertical-shift focus and Hard Negative Mining (e.g. electrical wires, concrete joints) via Albumentations.