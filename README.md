[🇺🇸 English](README.md) | [🇰🇷 한국어](README_KR.md)

# 🛸 Wall-E: Drone-Based Exterior Crack Detection System
> **Project Duration:** 2026.02.09 ~ 2026.02.25 (16 Days)

**Wall-E** is an automated inspection system that utilizes drone imagery to detect cracks and defects on building exteriors. Our solution leverages computer vision technology to identify, classify, and visualize structural anomalies, providing a safer and more efficient maintenance workflow.

---

## 👥 Team Structure & Roles

We operate as a cross-functional team with clearly defined responsibilities:

👉 **[View Project Kanban Board (GitHub Projects)](https://github.com/orgs/WallEproject/projects/1/views/1)**

| Role | Responsibilities | Key Focus Areas |
|------|------------------|-----------------|
| **Project Architecture (PA)** | System Architecture, Technical Direction, Documentation | Architecture Design, Tech Stack Selection, System Integration |
| **Backend Developer** | Server Architecture, API, DB Design | FastAPI, Supabase (PostgreSQL), REST API, Data Integrity |
| **AI Model Developer** | Model Training (YOLO), Optimization | Dataset Augmentation (Albumentations), Model Accuracy (mAP), Real-time Inference |
| **Frontend Developer** | Mobile App Development (Flutter) | Live Streaming View, Gallery UI, State Management, Responsive Design |

---

## 📅 Detailed Project Plan

### 1. 🧠 AI & Computer Vision Part
The core engine for real-time crack detection from drone footage.

*   **Model Selection**: YOLOv11n (Nano) - Optimized for real-time inference speed on mobile/edge devices.
*   **Dataset Construction**:
    *   **Source**: Public concrete crack datasets (e.g., AI Hub).
    *   **Merging**: Consolidating multiple COCO-format sources into a unified `merged_dataset`.
    *   **Augmentation**: Utilizing `Albumentations` to simulate drone conditions (Motion Blur, Noise, Brightness changes).
*   **Training Strategy**:
    *   Initially disabling default augmentations (Mosaic, etc.) and training exclusively on our custom "drone-adapted" augmented data to enhance domain adaptation.
    *   **Validation Metrics**: Focusing on mAP50 and Recall.

### 2. ⚙️ Backend & Architecture Part
The central server managing data flow and business logic.

*   **Framework**: FastAPI (Python) - Async processing and high-performance API.
*   **Database**: **Supabase (PostgreSQL)**
    *   **Missions**: Flight session management (Location name, Address, Timestamp).
    *   **Detections**: Crack detection info (Image URL, Confidence, **BBox JSON**, **GPS Coordinates**).
    *   **Users**: Integrated with Supabase Auth.
*   **Storage**: Supabase Storage - Storing high-resolution original crack images.
*   **Streaming**:
    *   **MediaMTX**: Receiving drone video via RTMP protocol.
    *   **StreamManager**: Reading frames via OpenCV, performing AI inference, and streaming overlay results to the app (MJPEG/HLS).

### 3. 📱 Frontend (App) Part
The interface for users to operate the drone and review inspection results.

*   **Framework**: Flutter (Dart) - Cross-platform (Android/iOS).
*   **Key Features**:
    *   **Real-time Monitoring**: Viewing live drone feed. Displaying bounding boxes when cracks are detected.
    *   **Mission Recording**: Controlling flight start/end, inputting site location (Building name).
    *   **Gallery**: Reviewing detected crack images list and details (Toggle Bounding Box On/Off).
    *   **Map Integration**: Google Maps Static API (Roadmap view) for mission site visualization.
    *   **Authentication**: User identification and data isolation using Supabase Auth.

### 4. 🗂 Data Pipeline Part
The complete flow from data collection to processing and storage.

1.  **Collection**: Drone Camera → RTMP → Backend Server.
2.  **Processing**:
    *   `StreamManager` captures frames.
    *   YOLOv11 model detects cracks (Confidence > 0.6).
3.  **Storage**:
    *   **Images**: Uploading raw original frames to storage.
    *   **Metadata**: Inserting BBox coordinates (x,y,w,h normalized), GPS, Labels into DB.
4.  **Visualization**: The app renders bounding boxes dynamically on the original image using the stored coordinates.

---

## 🛠 Tech Stack

### Core
*   **Language**: Python 3.10+, Dart 3.3+
*   **AI**: YOLOv11 (`ultralytics`), OpenCV, Albumentations
*   **Backend**: FastAPI, SQLAlchemy, PostgreSQL (`psycopg2`)
*   **Frontend**: Flutter 3.19+

### Infrastructure
*   **DB/Auth/Storage**: Supabase (Cloud)
*   **Streaming Server**: MediaMTX (RTMP/RTSP) - *Currently hosted on Team Member's Local Environment*
    *   **RTMP Port**: `1935` (Stream Input)
    *   **HLS Port**: `8888` (Stream Output)
    *   **API Port**: `9997` (Management)
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

# Key Dependencies (Installed automatically)
# fastapi==0.115.0
# uvicorn==0.32.0 - ASGI Server
# sqlalchemy==2.0.38 - ORM
# psycopg==3.3.2 - PostgreSQL Driver
# supabase==2.28.0 - Database Client
# ultralytics==8.3.0 - YOLOv11
# opencv-python==4.10.0.84 - Computer Vision
# python-dotenv==1.0.1 - Env Var Management
# pydantic==2.12.5 - Data Validation
```

#### Database (Supabase)
You must configure Supabase connection info in the `.env` file.
```env
DATABASE_URL=postgresql://user:pass@host:5432/postgres
RTMP_URL=rtmp://localhost:1935/live/test
```

### 2. Execution
#### RTMP Server (MediaMTX)
```bash
brew services start mediamtx   # Mac
# Or run the executable manually
```

#### Backend Server
```bash
uvicorn backend.main:app --reload
```

#### Frontend App
flutter run
```

---

## 🚀 Project Status & Recent Updates (2026.02.17)

### ✅ Completed Features
- **User Authentication**: Implemented secure Login/Signup flow with Supabase.
- **Korean Language Support**: Resolved UTF-8 encoding issues for Korean usernames and data.
- **Google Maps Integration**:
    - Replaced static placeholder with **Google Maps Static API**.
    - Applied **Roadmap** style for better visibility.
    - Implemented Real-time GPS coordinate display (N/S, E/W format).
- **Data Isolation**: Implemented Row Level Security logic to ensure users only see their own missions.
- **Android Configuration**:
    - Renamed package to `com.company.walle`.
    - Configured `AndroidManifest.xml` for Location permissions and API Keys.
- **Documentation**:
    - Refactored Role Definitions: Project Manager (PM) → **Project Architecture (PA)**.
    - Added comprehensive **Project Flow** and **Core Code Snippets** documentation.