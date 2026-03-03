# 리팩토링 및 정리 로그 (2026-02-16)

## 요약
프로젝트 구조를 리팩토링하여 유지보수성과 확장성을 개선했으며, 백엔드 조직화와 프론트엔드 타입 안정성에 중점을 두었습니다.

## 1. 백엔드 업데이트 (`/backend`)
- **디렉토리 구조**:
  - `ml_models/`: `.pt` 모델 파일을 이곳으로 이동 (예: `best_crack_model.pt`).
  - `scripts/`: 유틸리티 스크립트용 폴더 생성 (`init_db.py`, `check_db_connection.py`).
  - `tests/`: 테스트 파일 통합 (`test_api_flow.py`, `test_auth_flow.py`).
- **데이터베이스 스키마**:
  - `missions` 테이블에 `gps_lat` 및 `gps_lng` 필드 추가.
  - `detections` 테이블에서 GPS 필드 제거 (Mission으로 이동).
  - `backend/db/schema.sql`과 `backend/db/models.py` 동기화 완료.
- **코드 변경**:
  - Python 3.9 호환성 검증 (`api/auth.py`에서 `str | None`을 `Optional[str]`로 대체).
  - `core/stream_manager.py`가 새로운 `ml_models` 경로에서 모델을 로드하도록 수정.

## 2. 프론트엔드 업데이트 (`/frontend`)
- **타입 안정성**:
  - `models/` 디렉토리 도입:
    - `user_model.dart`
    - `mission_model.dart`
    - `detection_model.dart`
  - `ApiService.dart`가 `Map<String, dynamic>` 대신 타입 객체(예: `Future<Mission>`)를 반환하도록 리팩토링.
- **UI 리팩토링**:
  - `GalleryScreen`: `Mission` 객체를 사용하여 리스트를 렌더링하도록 재작성.
  - `MissionDetailScreen`: `Mission` 및 `Detection` 모델을 인자로 받도록 업데이트.
  - `ProfileScreen`: `User` 모델 속성을 사용하도록 업데이트.
  - `NewMissionScreen`: `Mission` 모델을 사용하여 네비게이션 처리.
- **기능 추가**:
  - `LiveStreamingScreen`에서 WebSocket을 통해 바운딩 박스 오버레이를 실시간으로 표시하는 기능 구현.

## 3. 검증
- `backend/tests/test_api_flow.py`를 성공적으로 실행하여 전체 API 수명 주기 확인:
  1. 미션 생성
  2. 감지 데이터 업로드
  3. GPS 업데이트 (미션 레벨)
  4. 데이터 조회

---
*2026-02-16 생성됨*
