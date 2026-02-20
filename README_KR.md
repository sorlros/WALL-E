[🇺🇸 English](README.md) | [🇰🇷 한국어](README_KR.md)

# 🛸 Wall-E: 드론 기반 외벽 균열 탐지 시스템
> **프로젝트 기간:** 2026.02.09 ~ 2026.02.25 (총 16일)

**Wall-E**는 드론 영상을 활용하여 건물 외벽의 균열 및 결함을 검사하는 자동화 시스템입니다. 우리의 솔루션은 컴퓨터 비전 기술을 통해 구조적 이상을 탐지, 분류 및 시각화하여 더 안전하고 효율적인 유지보수 워크플로우를 제공합니다.

---

## 👥 팀 구조 및 역할

우리는 아래와 같이 역할을 분담하여 프로젝트를 진행합니다.

👉 **[프로젝트 칸반 보드 확인하기 (GitHub Projects)](https://github.com/orgs/WallEproject/projects/1/views/1)**

| 역할 | 책임 (Responsibilities) | 주요 집중 분야 (Key Focus Areas) |
|------|------------------|-----------------|
| **Project Architecture (PA)** | 시스템 아키텍처, 기술 방향성 리딩, 문서화 | 아키텍처 설계, 기술 스택 선정, 시스템 통합 관리 |
| **Backend Developer** | 서버 아키텍처, API, DB 설계 | FastAPI, Supabase(PostgreSQL), REST API, 데이터 무결성 |
| **AI Model Developer** | 모델 학습 (YOLO), 최적화 | 데이터셋 증강(Albumentations), 모델 정확도(mAP), 실시간 추론 최적화 |
| **Frontend Developer** | 모바일 앱 개발 (Flutter) | 실시간 스트리밍 뷰, 갤러리 UI, 상태 관리, 반응형 디자인 |

---

## 📅 프로젝트 상세 계획 (Project Plan)

### 1. 🧠 AI & Computer Vision Part
드론 영상에서 실시간으로 균열(Crack)을 탐지하는 핵심 엔진입니다.

*   **모델 선정**: YOLOv11n (Nano) - 모바일/엣지 디바이스에서의 실시간 추론 속도 최적화.
*   **데이터셋 구축**:
    *   **소스**: AI Hub 등 공개된 콘크리트 균열 데이터셋.
    *   **병합 (Merge)**: 여러 소스의 COCO 포맷 데이터를 `merged_dataset`으로 통합.
    *   **증강 (Augmentation)**: `Albumentations`를 활용하여 드론 환경 모사 (Motion Blur, Noise, Brightness 변화).
*   **학습 전략**:
    *   초기에는 기본 증강(Mosaic 등)을 끄고, 우리가 만든 "드론 맞춤형 증강 데이터"로만 학습하여 도메인 적응력 강화.
    *   검증(Validation) 지표: mAP50, Recall 중점 관리.

### 2. ⚙️ Backend & Architecture Part
데이터 흐름과 비즈니스 로직을 담당하는 중앙 서버입니다.

*   **Framework**: FastAPI (Python) - 비동기 처리 및 고성능 API.
*   **Database**: **Supabase (PostgreSQL)**
    *   **Missions**: 비행 세션 관리 (장소명, 주소, 시간).
    *   **Detections**: 탐지된 크랙 정보 (이미지 URL, 신뢰도, **BBox JSON**, **GPS 좌표**).
    *   **Users**: Supabase Auth 연동.
*   **Storage**: Supabase Storage - 고해상도 원본 크랙 이미지 저장.
*   **Streaming**:
    *   **MediaMTX**: RTMP 프로토콜로 드론 영상 수신.
    *   **StreamManager**: OpenCV로 프레임을 읽어 AI 추론 후, 결과가 오버레이된 영상을 앱으로 송출 (MJPEG/HLS).

### 3. 📱 Frontend (App) Part
사용자가 드론을 조작하고 점검 결과를 확인하는 인터페이스입니다.

*   **Framework**: Flutter (Dart) - Android/iOS 크로스 플랫폼.
*   **주요 기능**:
    *   **실시간 관제**: 드론 시점의 영상을 실시간으로 확인. 크랙 탐지 시 화면에 박스 표시.
    *   **미션 기록**: 비행 시작/종료 제어, 현장 위치 정보(건물명) 입력.
    *   **갤러리**: 탐지된 크랙 이미지 리스트 확인, 상세 보기 (바운딩 박스 On/Off).
    *   **지도 연동**: Google Maps Static API (Roadmap)를 활용한 미션 위치 시각화 및 GPS 좌표 표시.
    *   **사용자 인증**: Supabase Auth 기반 로그인/회원가입 및 사용자별 데이터 격리.

### 4. 🗂 Data Pipeline Part
데이터의 수집부터 가공, 저장까지의 흐름입니다.

1.  **수집 (Collection)**: 드론 카메라 → RTMP → Backend Server.
2.  **처리 (Processing)**:
    *   `StreamManager`가 프레임 캡처.
    *   YOLOv11 모델이 크랙 탐지 (Confidence > 0.6).
3.  **저장 (Storage)**:
    *   이미지: 원본 프레임을 스토리지에 업로드.
    *   메타데이터: BBox 좌표(x,y,w,h 정규화값), GPS, 라벨 등을 DB에 Insert.
4.  **시각화 (Visualization)**: 앱에서 원본 이미지 위에 BBox 좌표를 기반으로 박스를 그려서 사용자가 확인.

---

## 🛠 기술 스택 (Tech Stack)

### Core
*   **Language**: Python 3.10+, Dart 3.3+
*   **AI**: YOLOv11 (`ultralytics`), OpenCV, Albumentations
*   **Backend**: FastAPI, SQLAlchemy, PostgreSQL (`psycopg2`)
*   **Frontend**: Flutter 3.19+

### Infrastructure
*   **DB/Auth/Storage**: Supabase (Cloud)
*   **Streaming Server**: MediaMTX (RTMP/RTSP) - *현재 팀원 로컬 환경에서 구동 중*
    *   **RTMP Port**: `1935` (영상 수신)
    *   **HLS Port**: `8888` (영상 송출)
    *   **API Port**: `9997` (서버 관리)
    *   **Stream Route (경로)**: `rtmp://<Server-IP>:1935/live/drone`

---

## 🌊 시작하기 (Getting Started)

### 1. 환경 설정
#### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 주요 설치 패키지 및 버전 (자동 설치됨)
# fastapi==0.115.0
# uvicorn==0.32.0 - ASGI 서버
# sqlalchemy==2.0.38 - ORM
# psycopg==3.3.2 - PostgreSQL 드라이버
# supabase==2.28.0 - 데이터베이스 클라이언트
# ultralytics==8.3.0 - YOLOv11 모델
# opencv-python==4.10.0.84 - 컴퓨터 비전 처리
# python-dotenv==1.0.1 - 환경변수 관리
# pydantic==2.12.5 - 데이터 검증
```

#### Database (Supabase)
`.env` 파일에 Supabase 접속 정보를 설정해야 합니다.
```env
DATABASE_URL=postgresql://user:pass@host:5432/postgres
RTMP_URL=rtmp://localhost:1935/live/test
```

### 2. 실행
#### RTMP 서버 (MediaMTX)
```드론앱에서 접속하는 서버주소
`rtmp://<Server-IP>:1935/live/drone`
```

#### Backend 서버
```bash
# backend 경로 진입 이후
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend 앱
flutter run
```

---

## 🚀 프로젝트 현황 및 최근 업데이트 (2026.02.17)

### ✅ 완료된 기능 (Completed)
- **사용자 인증 (Auth)**: Supabase 연동 로그인/회원가입 구현 완료.
- **한글 지원 강화**: 한글 사용자 이름 및 데이터의 UTF-8 인코딩 깨짐 현상 해결.
- **지도 연동 (Google Maps)**:
    - 정적 이미지 대신 **Google Maps Static API** 연동.
    - **Roadmap (일반 지도)** 스타일 적용으로 시인성 개선.
    - 실시간 GPS 좌표 표시 형식 개선 (N/S, E/W 표기).
- **데이터 격리**: 로그인한 사용자의 미션 데이터만 보이도록 백엔드/프론트엔드 필터링 적용.
- **Android 설정**:
    - 패키지명 변경: `com.company.walle`
    - 위치 권한 및 API 키 설정 완료.
- **문서화 (Documentation)**:
    - 역할 명칭 변경: PM → **PA (Project Architecture)** 로 변경 및 R&R 재정의.
    - **프로젝트 플로우(Project Flow)** 및 **핵심 코드 스니펫** 문서 추가.
