# Object Tracking (중복 저장 방지) 구현 상세 설명

이 문서는 드론 영상에서 동일한 균열이 반복적으로 저장되는 것을 방지하기 위해 적용된 **객체 추적(Object Tracking)** 기술과 코드 변경 사항을 설명합니다.

## 1. 구현 배경
- **기존 문제점**: 드론이 천천히 움직이거나 정지해 있을 때, 동일한 균열이 매 프레임마다 "새로운 균열"로 인식되어 데이터베이스에 무수히 많은 중복 데이터가 쌓이는 문제가 있었습니다.
- **해결 방안**: YOLO11n 모델의 **추적(Tracking)** 기능을 도입하여, 화면 속 객체에 고유 ID를 부여하고, 새로운 ID가 등장했을 때만 저장하도록 로직을 변경했습니다.

## 2. 주요 변경 사항

### 2.1 Backend (`backend/core/stream_manager.py`)

#### A. 추적 기능 활성화 (`model.track`)
기존의 단순 감지(`model()`) 대신 추적(`model.track()`) 함수를 사용하여 객체의 이동 경로를 추적합니다.

```python
# [변경 전]
# results = self.model(processed_frame, conf=0.5, verbose=False)

# [변경 후]
# persist=True 옵션은 다음 프레임에서도 ID를 유지하게 해줍니다.
results = self.model.track(processed_frame, conf=0.5, persist=True, verbose=False)
```

#### B. 고유 ID 관리 (`_processed_track_ids`)
이미 저장된 객체의 ID를 기억하기 위해 `Set` 자료구조를 사용합니다.

```python
# __init__ 메서드
self._processed_track_ids = set() # 저장된 ID 목록

# _capture_loop 메서드 (감지 루프)
if track_id not in self._processed_track_ids:
    if conf > 0.7:
        # 1. DB에 저장
        self._save_detection(frame, label, conf, bbox_norm)
        # 2. 처리된 ID 목록에 추가 (중복 방지)
        self._processed_track_ids.add(track_id)
        logger.info(f"🆕 [Tracking] New Object ID {track_id} Saved!")
```

#### C. 미션 시작/종료 시 초기화 (`start_mission`)
새로운 미션이 시작될 때마다 추적 ID 기록을 초기화하여, 이전 미션의 데이터가 영향을 주지 않도록 합니다.

```python
def start_mission(self, mission_id):
    """Start a new mission and reset tracking state."""
    self.active_mission_id = mission_id
    self._processed_track_ids.clear() # ID 목록 초기화
    logger.info(f"Started mission {mission_id}. Tracking IDs reset.")
    self.start()
```

---

### 2.2 Backend (`backend/api/missions.py`)

#### 미션 API 연동
미션 생성 API(`POST /missions`)와 종료 API(`POST /missions/{id}/complete`)에서 `StreamManager`의 새로운 메서드를 호출하도록 변경했습니다.

```python
# start_mission 호출 (미션 시작 시)
if stream_manager_instance:
    stream_manager_instance.start_mission(db_mission.id)

# stop_mission 호출 (미션 종료 시)
if stream_manager_instance:
    stream_manager_instance.stop_mission()
```

## 3. 기대 효과
1.  **데이터 효율성**: 동일한 균열은 단 한 번만 저장되므로 스토리지 용량을 획기적으로 절약합니다.
2.  **분석 정확도**: "균열 개수"를 셀 때, 중복된 이미지가 없으므로 정확한 통계를 낼 수 있습니다.
3.  **UI 성능**: 불필요한 DB 저장을 막아 서버 부하를 줄이고 WebSocket 전송을 최적화했습니다.
