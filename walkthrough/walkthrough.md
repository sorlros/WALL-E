# Wall-E 프로젝트 개발 업데이트 (2026-02-11)

오늘 수행한 **실시간 스트리밍, AI 자동 감지, 데이터베이스 구축, 갤러리 구현**에 대한 상세 작업 내용입니다.

## 🚀 주요 구현 기능

### 1. 🔍 AI 자동 감지 및 자동 저장 시스템
드론이 보내오는 실시간 영상을 백엔드(YOLOv8/11)가 분석하여, 균열이 감지되면 **자동으로** 이미지를 저장하는 시스템을 구축했습니다.

- **`StreamManager` 고도화**:
  - `yolo_model.predict()` 결과에서 `confidence > 0.6` 인 경우에만 저장 로직 발동
  - **중복 저장 방지(Cooldown)**: 같은 균열을 연속으로 저장하지 않도록 2초의 쿨다운 적용
  - 저장 경로: `backend/storage/images/YYYY-MM-DD/` (날짜별 자동 분류)

### 2. 🗄️ 데이터베이스 및 백엔드 API
데이터의 체계적인 관리를 위해 SQLite 데이터베이스와 SQLAlchemy ORM을 도입하고 RESTful API를 구현했습니다.

- **DB 스키마 설계**:
  - **`Users`**: 사용자 계정 (username, password_hash)
  - **`Missions`**: 미션 정보 (name, description, status, timestamp)
  - **`Detections`**: 감지된 결함 정보 (image_path, label, confidence, gps, timestamp)
- **API 엔드포인트 구현**:
  - `POST /missions/`: 미션 생성 (미션 시작 시 호출, 자동 감지 활성화)
  - `POST /missions/{id}/complete`: 미션 종료 (자동 감지 비활성화, 상태 업데이트)
  - `GET /missions/`: 전체 미션 목록 조회 (갤러리용)
  - `GET /storage/{path}`: 이미지 서빙 (StaticFiles Mount 완료)

### 3. 📱 플러터 앱 (Frontend) 기능 구현
백엔드 API와 연동하여 실제 드론 운용 시나리오에 맞는 UI/UX를 구현했습니다.

- **미션 생성 (`NewMissionScreen`)**:
  - 미션 이름과 메모를 입력하고 '미션 시작'을 누르면 API를 통해 미션을 생성하고 스트리밍 화면으로 전환됩니다.
- **실시간 스트리밍 (`LiveStreamingScreen`)**:
  - `flutter_mjpeg`를 사용해 지연 없는 실시간 영상 표시.
  - **미션 종료 버튼**: 누르면 API를 호출하여 백엔드의 자동 감지를 멈추고 미션을 '완료' 상태로 변경합니다.
- **갤러리 (`GalleryScreen` & `MissionDetailScreen`)**:
  - 수행한 미션 목록을 보여주고, 클릭 시 해당 미션에서 **AI가 자동 포착한 균열 이미지들**을 그리드로 확인 가능.
  - 이미지를 탭하면 원본 크기로 확대해서 볼 수 있습니다.

### 4. 🛠️ 데이터 병합 도구
- **`backend/scripts/merge_coco.py`**: 여러 팀원의 COCO 포맷 데이터셋(JSON+이미지)을 충돌 없이 하나로 병합하는 스크립트 작성 완료.

## 📁 수정된 파일 목록

### Backend (Python/FastAPI)
- `backend/core/stream_manager.py`: 실시간 YOLO 추론 및 자동 저장 로직 추가.
- `backend/api/missions.py`: 미션 생성/종료 및 `StreamManager` 제어 로직 추가.
- `backend/db/models.py`: DB 테이블 정의.
- `backend/db/database.py`: DB 연결 설정.
- `backend/main.py`: 정적 파일 서빙(`/storage`) 및 `StreamManager` 의존성 주입.
- `backend/scripts/merge_coco.py`: 데이터 병합 스크립트.

### Frontend (Flutter)
- `lib/services/api_service.dart`: 백엔드 통신 함수 (`createMission`, `completeMission`, `getMissions`) 추가.
- `lib/screens/new_mission_screen.dart`: 미션 생성 API 연동.
- `lib/screens/live_streaming_screen.dart`: 미션 종료 버튼 및 API 연동.
- `lib/screens/gallery_screen.dart`: 미션 목록 로딩 (`FutureBuilder`).
- `lib/screens/mission_detail_screen.dart`: [신규] 감지된 이미지 그리드 뷰.

---
**내일 예정 작업**:
1. 팀원 데이터 취합 후 `merge_coco.py`로 병합.
2. `coco_to_yolo.py`, `train_yolo.py` 작성 및 모델 재학습.
3. 구글 지도 API 연동 (GPS 좌표 시각화).
