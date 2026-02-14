# 🚀 Wall-E 프로젝트 개발 리포트 (2026-02-11)

오늘 작업한 **실시간 스트리밍 및 AI 자동 감지 시스템**의 전체 구조와 흐름을 시각화했습니다.
이 문서는 팀 내 공유 및 기능 검토용으로 작성되었습니다.

## 1. 🏗️ 시스템 아키텍처 (System Architecture)

드론 영상을 실시간으로 분석하여 균열을 감지하고, 앱에서 이를 확인하는 전체 구조입니다.

```mermaid
graph TD
    subgraph "Field (현장)"
        Drone[🚁 Drone] -- RTMP Stream --> MediaMTX[📡 MediaMTX Server]
    end

    subgraph "Backend (서버)"
        MediaMTX -- Stream Data --> StreamManager[⚡ StreamManager]
        StreamManager -- YOLOv8 Inference --> AI[🧠 AI Model]
        AI -- "Crack Detected (Conf > 60%)" --> Save[💾 Auto-Save]
        Save -- Image File --> Storage[📂 /storage/images]
        Save -- Metadata --> DB[(🗄️ SQLite DB)]
        
        API[🔌 FastAPI] -- Query --> DB
        API -- Serve Images --> Storage
    end

    subgraph "Frontend (앱)"
        App[📱 Flutter App] -- "1. Start Mission" --> API
        App -- "2. View Live Stream (MJPEG)" --> StreamManager
        App -- "3. Stop Mission" --> API
        App -- "4. View Gallery" --> API
    end
```

---

## 2. ⚡ 주요 기능 명세 (Key Features)

### A. 👁️ AI 자동 감지 로직 (Auto-Detection)
사람의 개입 없이 AI가 스스로 균열을 판단하고 저장합니다.

| 조건 | 동작 | 설명 |
| :--- | :--- | :--- |
| **Confidence > 0.6** | ✅ **저장** | YOLO 모델의 확신이 60% 이상일 때만 기록 |
| **Mission Active** | ✅ **저장** | 미션이 진행 중일 때만 기록 (유휴 상태 제외) |
| **Cooldown** | ⏳ **대기** | 중복 저장을 막기 위해 2초 간격으로 제한 |

### B. 📸 갤러리 및 데이터 시각화
저장된 데이터를 앱에서 직관적으로 확인할 수 있습니다.

| 화면 | 기능 | 비고 |
| :--- | :--- | :--- |
| **Live Streaming** | 실시간 영상 송출 + 미션 제어 | MJPEG 스트리밍 (지연 최소화) |
| **Gallery** | 수행한 미션 목록 조회 | 날짜별, 미션별 정리 |
| **Mission Detail** | **감지된 균열 이미지 그리드 뷰** | 클릭 시 원본 이미지 확대 |

---

## 3. 💾 데이터베이스 스키마 (Database Schema)

효율적인 데이터 관리를 위해 정규화된 테이블 구조를 설계했습니다.

```mermaid
erDiagram
    USERS ||--o{ MISSIONS : "creates"
    MISSIONS ||--o{ DETECTIONS : "contains"
    
    USERS {
        int id PK
        string username
        string password_hash
    }

    MISSIONS {
        int id PK
        string name "미션명"
        string description "메모"
        string status "active / completed"
        datetime created_at
    }

    DETECTIONS {
        int id PK
        int mission_id FK
        string image_path "이미지 파일 경로"
        string label "균열 종류 (crack 등)"
        float confidence "AI 신뢰도"
        float gps_lat "위도"
        float gps_lng "경도"
        datetime created_at
    }
```

---

## 4. 🔄 미션 수행 프로세스 (Workflow)

사용자가 앱을 통해 미션을 수행하는 전체 과정입니다.

```mermaid
sequenceDiagram
    participant User as 👤 사용자
    participant App as 📱 앱 (Frontend)
    participant Server as 🖥️ 백엔드 (Backend)
    participant AI as 🧠 AI (YOLO)
    participant DB as 🗄️ 데이터베이스

    User->>App: 미션 정보 입력 & 시작
    App->>Server: POST /missions (생성)
    Server->>DB: 미션 레코드 생성 (Active)
    Server-->>App: 미션 ID 반환
    
    User->>App: 스트리밍 화면 이동
    App->>Server: 실시간 영상 요청
    
    loop Live Streaming & Detection
        Server->>AI: 프레임 분석 요청
        AI-->>Server: 결과 반환 (Label, Conf)
        
        alt Conf > 0.6 & Cooldown OK
            Server->>Server: 이미지 파일 저장
            Server->>DB: Detection 정보(이미지 경로, 점수) 저장
        end
        
        Server-->>App: MJPEG 프레임 전송
    end

    User->>App: 미션 종료 버튼 클릭
    App->>Server: POST /missions/{id}/complete
    Server->>DB: 미션 상태 'Completed'로 변경
    Server-->>App: 종료 확인

    User->>App: 갤러리 확인
    App->>Server: GET /missions (목록 요청)
    Server-->>App: 미션 목록 반환
```

---

## 5. ✅ 금일 작업 완료 파일 (Created/Modified Files)

### Backend
- `backend/core/stream_manager.py`: 자동 감지 및 쿨다운 로직 구현
- `backend/api/missions.py`: 미션 제어 API
- `backend/db/models.py`: DB 스키마 정의
- `backend/main.py`: 정적 파일 서빙 설정
- `backend/scripts/merge_coco.py`: 학습 데이터 병합 스크립트

### Frontend
- `lib/services/api_service.dart`: API 연동 서비스
- `lib/screens/live_streaming_screen.dart`: 스트리밍 화면 & 종료 기능
- `lib/screens/gallery_screen.dart`: 미션 목록 UI
- `lib/screens/mission_detail_screen.dart`: 감지 결과 상세 보기 (신규)

---
**내일 예정 작업 (Next Steps)**
1. 🔗 팀원 데이터 취합 및 `merge_coco.py` 병합 실행 (오전)
2. 🏋️‍♂️ 병합된 데이터로 YOLOv11 모델 추가 학습 (오후)
3. 🗺️ 구글 지도 API 연동 (오후)
