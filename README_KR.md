[🇺🇸 English](README.md) | [🇰🇷 한국어](README_KR.md)

# 🛸 Wall-E: 드론 기반 외벽 균열 탐지 시스템
> **프로젝트 기간:** 2026.02.09 ~ 2026.02.25 (총 16일)

**Wall-E**는 드론 영상을 활용하여 건물 외벽의 균열 및 결함을 검사하는 자동화 시스템입니다. 우리의 솔루션은 컴퓨터 비전 기술을 통해 구조적 이상을 탐지, 분류 및 시각화하여 더 안전하고 효율적인 유지보수 워크플로우를 제공합니다.

---

## 👥 팀 구조 및 역할

우리는 4명의 팀원으로 구성된 다기능 팀(Cross-functional team)으로 운영되며, 애자일 개발과 고품질 결과물 산출을 위해 명확한 역할 분담을 따릅니다.

| 역할 | 책임 (Responsibilities) | 주요 집중 분야 (Key Focus Areas) |
|------|------------------|-----------------|
| **Project Manager (PM)** | 제품 비전, 일정 관리, 요구사항 정의 | 사용자 스토리, 스프린트 계획, 문서화, 이해관계자 소통 |
| **Backend Developer** | 서버 아키텍처, API 설계, 데이터베이스 관리 | FastAPI/Django, REST/GraphQL 설계, 데이터 무결성, 클라우드 배포 |
| **AI Model Developer** | 모델 학습 (YOLO), 최적화, 추론 로직 | 데이터셋 전처리, 모델 정확도(mAP), 실시간 처리 속도 |
| **UI/UX Developer** | 모바일 앱 개발, 사용자 인터페이스 디자인 | Flutter 구현, 사용자 경험 흐름, 반응형 디자인, 상태 관리 |

---

## 🛠 기술 스택 및 버전 표준

로컬 환경 및 CI/CD 파이프라인의 일관성을 위해 모든 팀원은 다음 버전 표준을 **반드시** 준수해야 합니다.

### 핵심 환경 (Core Environment)
- **Python:** `3.10.12` (AI/Backend 일관성 유지 필수)
- **Java (JDK):** `17` (LTS - Android 빌드 및 백엔드 호환성 필수)
- **Node.js:** `LTS (v20.x)` (툴링에 필요시)

### 모바일 앱 (Frontend)
- **Framework:** **Flutter 3.19.x**
- **Dart:** `3.3.x`
- **Minimum Target SDK:** Android API 26 / iOS 12.0

### AI & 컴퓨터 비전 (AI & Computer Vision)
- **Library:** **OpenCV 4.9.0** (서버용 Headless, 로컬 디버그용 Full)
- **Model:** **YOLOv8** (`ultralytics` 패키지 8.1.x)
- **CUDA:** `11.8` 혹은 `12.1` (PyTorch 버전 호환성 확인)

### 백엔드 & 프로토콜 (Backend & Protocol)
- **Communication:** RTSP/RTMP (실시간 비디오 스트리밍)
- **API Style:** RESTful API (JSON)
- **Database:** PostgreSQL (v15) / Redis (캐싱)

---

## 🌊 워크플로우 및 컨벤션

### 프로젝트 관리 (Project Management)
[프로젝트 보드 바로가기](https://github.com/orgs/WallEproject/projects/1/views/1)

### Git Flow
우리는 코드베이스를 효과적으로 관리하기 위해 **Git Flow** 전략을 따릅니다.
- `main`: 배포 가능한 프로덕션 코드. 보호된 브랜치(Protected branch).
- `develop`: 기능 통합 브랜치.
- `feature/*`: 기능별 개발 브랜치 (예: `feature/login-screen`, `feature/yolo-model-training`).

### 🌿 Branch Strategy

모든 팀원은 아래의 브랜치 네이밍 규칙을 준수하여 작업합니다.

| 구분 | 브랜치 이름 예시 (Prefix/Topic) | 주요 작업 내용 |
| :--- | :--- | :--- |
| **PM (Docs/Env)** | `docs/prd-update`, `env/set-gitignore` | 문서화, 공통 환경 설정 관리 |
| **AI 개발자** | `feature/ai-yolo-v8-train`, `feature/ai-mask-overlay` | 모델 학습, 결과 시각화 로직 |
| **백엔드/드론** | `feature/drone-rtsp-stream`, `fix/drone-connection-lag` | 드론 영상 수신, 통신 버그 수정 |
| **프론트 (App)** | `feature/app-main-ui`, `feature/app-video-widget` | 앱 레이아웃, 영상 출력 화면 |

**※ 주의:** 모든 기능 개발은 `develop` 브랜치에서 파생(Checkout)하며, 완료 후 `develop`으로 PR을 보냅니다.

### Commit Message Convention
[Conventional Commits](https://www.conventionalcommits.org/) 사양을 따라주세요:
- `add`: 새로운 기능 추가
- `delete`: 기존 코드 삭제
- `fix`: 버그 수정
- `update`: 기존 코드 업데이트
- `docs`: 문서 변경
- `style`: 코드 의미에 영향을 주지 않는 변경 (공백, 포맷팅 등)
- `refactor`: 버그 수정이나 기능 추가가 아닌 코드 변경


---

## 🚀 시작하기 (Getting Started)

### 1. 사전 요구사항 (Prerequisites)
Python, Java, Flutter의 필수 버전이 설치되어 있는지 확인해주세요.

### 2. 저장소 복제 (Clone Repository)
```bash
git clone https://github.com/WallEproject/WallE.git
cd skypatch
```

### 3. 설정 예시 (Setup Example)
```bash
# Python 가상환경 설정
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
