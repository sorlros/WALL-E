[🇺🇸 English](README.md) | [🇰🇷 한국어](README_KR.md)

# 🛸 Wall-E: 드론 기반 외벽 균열 탐지 시스템
> **프로젝트 기간:** 2026.02.09 ~ 2026.02.25 (총 16일)

**Wall-E**는 드론 영상을 활용하여 건물 외벽의 균열 및 결함을 검사하는 자동화 시스템입니다. 우리의 솔루션은 컴퓨터 비전 기술과 초융합 멀티스레드 스트리밍 아키텍처를 통해 구조적 이상을 탐지, 분류 및 시각화하여 더 안전하고 효율적인 유지보수 워크플로우를 제공합니다.

---

## 🏗️ 시스템 아키텍처 (System Architecture)

드론에서 촬영된 영상이 사용자의 스마트폰(Flutter 앱)으로 스트리밍 되며, 중간 매개체인 백엔드 영상 서버에서 실시간 AI 분석 및 중복 필터링이 일어납니다.

```mermaid
graph TD
    Drone["🚁 드론 (DJI Phantom 4 Pro)"]
    RTMP["📡 미디어 서버 (MediaMTX)<br/>[RTMP 1935]"]
    Backend["💻 백엔드 서버 (FastAPI/Python)<br/>[HTTP 8000]"]
    DB[("🐘 데이터베이스<br/>(Supabase PostgreSQL)")]
    App["📱 클라이언트 앱 (Flutter)<br/>[Android/iOS]"]

    Drone -- "1. 원본 영상 송출<br/>(1080p, 60fps)" --> RTMP
    RTMP -- "2. 비디오 스트림 풀링" --> Backend
    Backend -- "4. AI 추론 및 처리 결과 저장<br/>(Mission, Detections)" --> DB
    Backend -- "3. 모바일 최적화 송출<br/>(MJPEG, 720p 30fps)" --> App
    App -- "5. API 관리 요청" --> Backend
    App -- "6. 갤러리 이미지 로드" --> DB
```

---

## 👥 팀 구조 및 역할

👉 **[프로젝트 칸반 보드 확인하기 (GitHub Projects)](https://github.com/orgs/WallEproject/projects/1/views/1)**

| 역할 | 책임 (Responsibilities) | 주요 집중 분야 (Key Focus Areas) |
|------|------------------|-----------------|
| **Project Architecture (PA)** | 시스템 아키텍처, 기술 방향성 리딩, 문서화 | 3-Track 비동기 아키텍처 설계, 기술 스택 선정, 시스템 통합 관리 |
| **Backend Developer** | 서버 아키텍처, API, DB 설계 | FastAPI, Supabase, REST API, StreamManager 멀티스레드 최적화 |
| **AI Model Developer** | 모델 학습(YOLO), Re-ID 로직 | Albumentations 증강, MobileNetV3 임베딩 추출, 실시간 추론 최적화 |
| **Frontend Developer** | 모바일 앱 개발 (Flutter) | 플로팅 캡처(FAB), MJPEG 실시간 스트리밍 뷰, 상태 관리 |

---

## 📅 프로젝트 핵심 파이프라인 (Project Pipeline)

### 1. 🧠 AI & Computer Vision Part
드론 영상에서 실시간으로 균열(Crack)을 찾고 중복을 거르는 핵심 엔진입니다.
*   **객체 탐지 (Object Detection)**: YOLO11n (Nano) - 초고속 실시간 형태 인식.
*   **중복 균열 필터링 (Re-Identification)**: `MobileNetV3-small` 모델 기반.
    *   동일한 균열이 드론 흔들림에 의해 여러 장 찍히는 것을 방지합니다.
    *   균열 부분을 잘라내어(Crop) 576차원 임베딩으로 변환 후, 최근 캐시와 **코사인 유사도(Cosine Similarity)**를 비교해 80% 이상 일치 시 저장을 무시(Drop)합니다.
*   **데이터셋 증강 (Augmentation)**:
    *   `Albumentations`를 활용하여 수직 비행 흔들림(Shift), 잔상(Motion Blur), 역광 등을 완벽하게 모사합니다.
    *   Hard Negative Mining을 통해 전선, 타일 이음새 등 가짜 균열 사진들을 Background 클래스로 추가하여 오탐지를 획기적으로 낮췄습니다.

### 2. ⚙️ Backend & Architecture Part
스레드 병목을 없애 지연 시간(Zero Latency)을 달성한 3-Track 비동기 아키텍처입니다.
*   **Thread 1 (카메라 수신 전문)**: 영상 인코딩/AI 연산을 배제하고 오직 메모리에 최신 드론 프레임을 퍼나르는 버퍼 방어 역할.
*   **Thread 2 (AI 추론 전문)**: 최신 프레임을 도둑질해 YOLO 추론 후 BBox 업데이트 + Re-ID 필터링 + 수동 캡처 이미지 DB 비동기 저장.
*   **Thread 3 (모바일 송출 전문)**: 1번 스레드의 사진과 2번 스레드의 박스 좌표를 합성하여 720p 30FPS로 화질을 최적화해 스마트폰에 MJPEG로 쏘아줌.
*   **Database & Storage**: Supabase (PostgreSQL) - 탐지 내역, 모바일 사용자 인증(Auth), 이미지 스토리지 통합.

### 3. 📱 Frontend (App) Part
사용자가 딜레이 없이 영상을 관제하고 드론을 제어하는 인터페이스입니다.
*   **실시간 관제**: `flutter_mjpeg` 라이브러리를 통해 블랙스크린 및 메모리 누수 없이 30FPS 완벽 재생.
*   **수동 캡처 (Manual Capture)**: 실시간 영상 관제 중 사용자가 위험 요소를 직접 버튼(FAB)으로 찍어 DB (is_manual=true)에 기록 및 별도 뱃지 표기.
*   **갤러리 & 지도 연동**: Google Maps 화면으로 미션 위치를 확인하고, 탐지 결과(BBox On/Off)를 직관적으로 분석.

---

## 🛠 기술 스택 (Tech Stack)

### Core
*   **Language**: Python 3.10+, Dart 3.3+
*   **AI**: YOLOv11 (`ultralytics`), PyTorch (`MobileNetV3`), OpenCV, Albumentations
*   **Backend**: FastAPI, SQLAlchemy, PostgreSQL (`psycopg2`)
*   **Frontend**: Flutter 3.19+

### Infrastructure
*   **DB/Auth/Storage**: Supabase (Cloud)
*   **Streaming Server**: MediaMTX (RTMP)
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
```
> ※ AI 오프라인 모델 (`backend/models/mobile_net_v3_small.pth`)이 필요합니다.

#### Database 연동
`.env` 파일에 Supabase 접속 정보를 설정해야 합니다.
```env
DATABASE_URL=postgresql://user:pass@host:6543/postgres
SUPABASE_URL=...
SUPABASE_KEY=...
RTMP_URL=rtmp://localhost:1935/live/drone
```

### 2. 실행
#### RTMP 미디어 서버 (MediaMTX)
* 현재 **팀원의 데스크탑 환경**에 Windows/Linux용 `mediamtx`가 설치되어 운영 중입니다.
* 드론과 백엔드 서버가 해당 데스크탑으로 접근할 수 있도록 **포트포워딩(Port Forwarding)** 설정이 1935번 포트에 완료되어 있습니다.
* 모델/백엔드를 담당하는 본 Mac 환경에서는 미디어 서버를 직접 켤 필요가 없습니다.

#### Backend 서버
```bash
# backend 경로 진입 이후
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 앱 실행
cd frontend
flutter run -d R3CY30EEH2R
```

---

## 🚀 개발 연혁 (Development Timeline)

### 📍 2026.02.11 ~ 02.13 (Phase 1: 인프라 및 기반 시스템 구축)
- **통합 DB/Auth 구축**: Supabase PostgreSQL 기반 스키마 설계 및 로그인/회원가입 API 구현 완료.
- **실시간 스트리밍 베이스라인**: MediaMTX 인프라 연동, OpenCV기반 프레임 캡처 및 화면 내 Bounding Box 오버레이 기초 구현.
- **객체 추적(Object Tracking) 초기 도입**: 드론 정지 시 중복 방지를 위한 YOLO `model.track()` 기능 및 식별 ID 저장(Set) 로직 적용.
- **앱 UI 네비게이션**: 새 미션/갤러리/프로필로 이어지는 Flutter 클라이언트 기본 라우팅 체계 완성.

### 📍 2026.02.16 (Refactoring Day & UX 개선)
- **프론트엔드 타입 안정성 확보**: Dart 내 `Mission`, `Detection`, `User` 모델 클래스를 생성하여 API 응답을 타입 세이프하게 관리.
- **제로 딜레이 아키텍처 및 BBox 정렬(Ratio Fix)**: 추론 패딩 전처리를 제거하고 원본 프레임 좌표를 매핑하여 기기별 화면 비율에 따른 바운딩 박스 밀림 현상 완벽 해결.
- **갤러리 UI 고도화**: 상세조회 화면에 스와이프 내비게이션(PageView) 적용 및 가로/세로 모드 대응 반응형 레이아웃 구현.
- **백엔드 메타데이터 구조 개선**: `detections` 테이블에 있던 GPS 데이터를 `missions` 테이블 계층으로 상향 조정하여 구조 최적화.

### 📍 2026.02.17 ~ 02.19 (Phase 2: 스트리밍 패러다임 전환 및 데이터 보안)
- **지도 연동 (Google Maps)**: Google Maps Static API를 연동하여 실제 미션 위치(Roadmap) 및 GPS 좌표 모니터링 시각화.
- **데이터 격리 (Data Isolation)**: Supabase RLS 적용 및 백엔드 필터링으로 로그인한 사용자의 데이터만 접근 가능하도록 보안 강화.
- **스트리밍 프로토콜 전환 (HLS ➔ MJPEG)**: 기존 HLS의 태생적 버퍼링 지연(3~5초)과 WebSocket 좌표 간의 싱크 어긋남(Desync)을 물리적으로 해결하기 위해 백엔드 영상 합성(Burn-in) 송출 방식으로 전면 개편.
- **OpenCV 백엔드 최적화**: Mac(Apple Silicon) 및 서버 환경의 호환성/안정성을 위해 `CAP_FFMPEG` 강제 할당을 해제하여 하드웨어 가속 확보.
- **사용자 경험(UX) 버그 수정**: 한글 사용자 이름 및 데이터의 UTF-8 인코딩 깨짐 현상 완벽 해결, 안드로이드 위치 권한 설정 완료.

### 📍 2026.02.20 (Phase 3: 실시간 성능 극대화 및 AI 고도화)
- **3-Track 비동기 스트리밍 설계**: 수신/AI추론/송출 스레드를 완벽히 분리하여 병목 시 발생하는 끊김 현상(Stuttering)을 없애고 Zero-Latency 달성.
- **모바일 스트리밍 최적화**: `flutter_mjpeg` 패키지 도입 및 스마트폰 대역폭을 고려한 백엔드 720p 30fps 리사이징으로 앱 내 블랙스크린 및 과부하 해결.
- **MobileNetV3 중복 필터링 (Re-ID)**: YOLO 트래킹 ID의 추적 한계를 극복하기 위해, 임베딩 코사인 유사도 연산(80% Threshold, 10% Margin)을 통한 딥러닝 기반 재식별 시스템 구비.
- **수동 캡처(Manual Capture) 연동**: 라이브 뷰 화면 내 플로팅 버튼(FAB)으로 사용자 수동 점검 기록 기능 및 식별 뱃지 추가.
- **데이터 증강 전략 수립**: Albumentations 적용 (상하 흔들림, 잔상) 및 Hard Negative Mining(전선, 메지 등 함정 객체를 Background로 혼합) 기법 설계.
