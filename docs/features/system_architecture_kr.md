# Wall-E 프로젝트 시스템 아키텍처 (System Architecture)

본 문서는 Wall-E (외벽 균열을 점검하는 무인 드론 시스템)의 전체 데이터 흐름과 시스템 컴포넌트 간의 상호작용을 정리한 종합 아키텍처 가이드입니다.

## 1. 전체 시스템 구성도 (System Overview)

드론에서 촬영된 영상이 사용자의 스마트폰(Flutter 앱)으로 스트리밍 되며, 중간 매개체인 백엔드 영상 서버에서 실시간 AI 분석 및 중복 필터링이 일어나는 3-Tier 구조입니다.

```mermaid
graph TD
    %% 노드 정의
    Drone["🚁 드론 (DJI Phantom 4 Pro)"]
    RTMP["📡 미디어 서버 (MediaMTX)<br/>[RTMP 1935]"]
    Backend["💻 백엔드 서버 (FastAPI/Python)<br/>[HTTP 8000]"]
    DB[("🐘 데이터베이스<br/>(Supabase PostgreSQL)")]
    App["📱 클라이언트 앱 (Flutter)<br/>[Android/iOS]"]

    %% 데이터 흐름
    Drone -- "1. 원본 라이브 영상 송출<br/>(1080p, 60fps)" --> RTMP
    RTMP -- "2. 비디오 스트림 풀링" --> Backend
    Backend -- "4. AI 추론 및 처리 결과 저장<br/>(Mission, Detections)" --> DB
    Backend -- "3. 최적화된 화면 송출<br/>(MJPEG, 720p 30fps)" --> App
    App -- "5. API 요청 (수동 캡처, 미션 조회 등)" --> Backend
    App -- "6. 갤러리 이미지 로드" --> DB
```

---

## 2. 🚀 백엔드 핵심 스트리밍 파이프라인 (3-Track 비동기 아키텍처)

가장 연산량이 복잡하고 아키텍처의 핵심인 `StreamManager` (`stream_manager_ai_only.py`) 내부의 흐름도입니다. 
영상 수신, AI 연산, 클라이언트 송출 병목을 막기 위해 **3개의 쓰레드(일꾼)가 비동기(Asynchronous)로 완벽히 분리**되어 동작합니다.

```mermaid
sequenceDiagram
    participant Camera as 🎥 Thread 1: Camera Loop (수신 전담)
    participant AI as 🧠 Thread 2: Inference Loop (AI 추론 전담)
    participant ReID as 🔍 Re-ID Manager (중복 필터링)
    participant DB as 💾 Database / Storage
    participant API as 🌐 Thread 3: API Route (송출 전담)
    participant App as 📱 Flutter App

    Note over Camera, App: [비동기 멀티스레딩] 병목이 발생하지 않도록 독립적으로 무한 반복
    
    %% 카메라 수신 스레드
    loop 60 FPS
        Camera->>Camera: RTMP 읽기 (cap.read)
        Camera--)AI: 최신 프레임 메모리 갱신 (Lock)
    end

    %% AI 추론 및 필터링 스레드
    loop ~25 FPS (YOLO Speed)
        AI->>AI: 1. YOLOv11n 추론 (박스 찾기)
        opt 균열(Confidence > 0.70) 발견 시
            AI->>ReID: 2. 박스 부분만 자르기(Crop + Margin 10%)
            ReID->>ReID: 3. MobileNetV3 임베딩 추출
            ReID->>ReID: 4. 기존 캐시와 코사인 유사도 연산
            
            alt 유사도 >= 0.80 (중복)
                ReID-->>AI: Drop (저장 안 함)
            else 유사도 < 0.80 (신규 균열)
                AI->>DB: 5. 이미지 JPG 캡처본 저장
                AI->>DB: 6. Detection(균열 정보) Row 생성
                ReID->>ReID: 7. 새 임베딩을 캐시에 기억 (Add)
            end
        end
        AI--)API: 최신 박스 좌표 업데이트 (Lock)
    end

    %% 모바일 송출 스레드
    loop 30 FPS (모바일 최적화)
        API->>API: Thread 1의 사진 + Thread 2의 박스 병합
        API->>API: 720p 리사이징 & JPG 인코딩 (MJPEG)
        API-->>App: 실시간 프레임 전송
    end

    %% 수동 캡처 (Manual Capture FAB) 이벤트
    App->>API: POST /missions/{id}/capture (수동 캡처 버튼 클릭)
    API->>AI: 현재 프레임 훔쳐오기
    AI->>DB: is_manual=True 로 DB 즉시 저장
```

---

## 3. 기능/기술 스택 별 핵심 컴포넌트

### 3.1 💻 AI 영상 분석 (Backend)
- **프레임워크:** Python `FastAPI`, `Uvicorn`
- **객체 탐지 (Object Detection):** `Ultralytics YOLO11n` (사용자 정의 학습 모델 - 균열 탐지)
- **중복 균열 필터 (Re-Identification):** `PyTorch` + `MobileNetV3-small` (오프라인 로컬 가중치 사용)
- **영상 처리:** `OpenCV (cv2)` 
- **DB ORM:** `SQLAlchemy` (PostgreSQL)

### 3.2 📱 사용자 앱 (Frontend)
- **프레임워크:** `Flutter`, `Dart`
- **실시간 비디오 렌더링:** `flutter_mjpeg` 패키지를 통한 MJPEG 초고속 렌더링. 블랙스크린 및 메모리 누수 방지.
- **주요 화면:** 
  - **새 미션 화면 (드론 연결):** 실시간 드론 배터리/신호 상태 연동 준비
  - **라이브 스트리밍 화면:** AI 오버레이 영상 재생 및 🙋‍♂️ `수동 캡처(Manual Capture) FAB` 버튼 기능
  - **결과 조회 화면 (Gallery):** 미션별 통계 및 AI 자동 저장 균열 / 수동 식별 사진 리스트 조회 기능

### 3.3 💾 데이터베이스 (Supabase)
- **관계형 Database (PostgreSQL):**
  - `Mission` 테이블: 탐지 날짜 등 종합 메타 정보
  - `Detection` 테이블: AI가 찾아낸 좌표(bbox), 신뢰도(confidence), 이미지 경로, `is_manual(수동캡처 여부)` 플래그 기록
- **Storage:** 균열이 발견된 원본 캡처 JPG 파일들이 날짜별로 누적 적재되는 볼륨 스토리지.
