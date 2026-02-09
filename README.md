[🇺🇸 English](README.md) | [🇰🇷 한국어](README_KR.md)

# 🛸 Wall-E: Drone-based Exterior Crack Detection System
> **Project Duration:** 2026.02.09 ~ 2026.02.25 (Half Month)

**Wall-E** is an automated system designed to inspect building exteriors for cracks and defects using drone imagery. Our solution leverages computer vision to detect, classify, and visualize structural anomalies, ensuring safer and more efficient maintenance workflows.

---

## 👥 Team Structure & Roles

We operate as a cross-functional team of 4, with clear responsibilities to ensure agile development and high-quality deliverables.

| Role | Responsibilities | Key Focus Areas |
|------|------------------|-----------------|
| **Project Manager (PM)** | product vision, scheduling, requirements definition | User stories, Sprint planning, Documentation, Stakeholder communication |
| **Backend Developer** | Server architecture, API design, Database management | FastAPI/Django, REST/GraphQL design, Data integrity, Cloud deployment |
| **AI Model Developer** | Model training (YOLO), Optimization, Inference logic | Dataset preparation, Model accuracy (mAP), Real-time processing speed |
| **UI/UX Developer** | Mobile app development, User Interface design | Flutter implementation, User experience flow, Responsive design, State management |

---

## 🛠 Tech Stack & Version Standards

To ensure consistency across local environments and CI/CD pipelines, all team members **must** adhere to the following version standards.

### Core Environment
- **Python:** `3.10.12` (Required for AI/Backend consistency)
- **Java (JDK):** `17` (LTS - Required for Android build & backend compatibility)
- **Node.js:** `LTS (v20.x)` (If required for tooling)

### Mobile App (Frontend)
- **Framework:** **Flutter 3.19.x**
- **Dart:** `3.3.x`
- **Minimum Target SDK:** Android API 26 / iOS 12.0

### AI & Computer Vision
- **Library:** **OpenCV 4.9.0** (Headless for server, full for local debug)
- **Model:** **YOLOv8** (via `ultralytics` package 8.1.x)
- **CUDA:** `11.8` or `12.1` (Ensure compatibility with PyTorch version)

### Backend & Protocol
- **Communication:** RTSP/RTMP (Real-time video streaming)
- **API Style:** RESTful API (JSON)
- **Database:** PostgreSQL (v15) / Redis (Caching)

---

##  Workflow & Conventions

### Project Management
[View Project Board](https://github.com/orgs/WallEproject/projects/1/views/1)

### Git Flow
We follow the **Git Flow** strategy to manage our codebase effectively.
- `main`: Production-ready code. Protected branch.
- `develop`: Integration branch for features.
- `feature/*`: Feature-specific branches (e.g., `feature/login-screen`, `feature/yolo-model-training`).

### 🌿 Branch Strategy

All team members must follow the branch naming conventions below.

| Role | Branch Name Example (Prefix/Topic) | Key Tasks |
| :--- | :--- | :--- |
| **PM (Docs/Env)** | `docs/prd-update`, `env/set-gitignore` | Documentation, Common environment setup |
| **AI Developer** | `feature/ai-yolo-v8-train`, `feature/ai-mask-overlay` | Model training, Result visualization logic |
| **Backend/Drone** | `feature/drone-rtsp-stream`, `fix/drone-connection-lag` | Drone video streaming, Communication bug fixes |
| **Frontend (App)** | `feature/app-main-ui`, `feature/app-video-widget` | App layout, Video display widget |

**Note:** All feature development must branch off from `develop`, and PRs must be sent to `develop` upon completion.

### Commit Message Convention
Please follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have the required versions of Python, Java, and Flutter installed.

### 2. Clone Repository
```bash
git clone https://github.com/WallEproject/WallE.git
cd skypatch
```

### 3. Setup (Example)
```bash
# Python Environment
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```