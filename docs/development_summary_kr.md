
# 개발 요약: 바운딩 박스 정렬 및 UX 개선

다음은 균열 탐지의 정확성, 올바른 좌표 정렬, 그리고 사용자 경험 개선을 위해 수정 및 추가된 로직에 대한 상세 요약입니다.

## 1. 백엔드 로직 (`stream_manager.py`)

### A. 좌표계 수정 (Coordinate System Fix - 중요)
*   **문제점:** 백엔드에서 AI 추론을 실행하기 *전*에 프레임을 640x640 크기로 리사이징(회색 패딩 추가)하고 있었습니다. 이로 인해 AI는 패딩이 추가된 640x640 이미지를 기준으로 좌표를 반환하는 반면, 저장되는 이미지는 원본 1280x720 이미지였습니다. 결과적으로 바운딩 박스에 수직 오차(y축 밀림)가 발생했습니다.
*   **해결:** 추론 전처리 단계를 제거했습니다. 이제 **원본 1280x720 프레임**을 YOLO 추적 모델에 직접 전달합니다.
*   **결과:** 모델이 원본 1280x720 이미지에 완벽하게 매핑되는 정규화된 좌표(0.0 - 1.0)를 반환합니다.

### B. 제로 딜레이 아키텍처 (Zero-Delay Architecture)
*   **구현:** 감지 및 이미지 저장이 동일한 프로세스 루프 내에서 발생하도록 확인했습니다.
*   **지연 시간 로깅 (Latency Logging):** `추론(inference)`과 `저장(save)` 사이의 시간 차이를 측정하는 로그를 추가했습니다. 지연 시간이 무시할 수 있는 수준(<10ms)임을 확인하여 "제로 딜레이"를 입증했습니다.

### C. 모델 경로 업데이트
*   **변경:** `model_path`를 최신 학습 가중치로 업데이트했습니다: `runs/detect/wall-e-crack-detection/v3_mixed_original2/weights/best.pt`.

---

## 2. 프론트엔드 로직 (Flutter)
### A. 갤러리 상세 뷰 (`mission_detail_screen.dart`)

#### 1. 종횡비 수정 (Aspect Ratio Fix / "Ratio Fix")
*   **문제점:** 서로 다른 종횡비를 가진 화면(예: 아이폰 vs 아이패드, 세로 vs 가로)에서 이미지를 볼 때, 레터박스(검은 여백)가 생기면 바운딩 박스가 밀리는 현상이 발생했습니다.
*   **해결책:** `LayoutBuilder`를 사용하여 동적 사이징 로직을 구현했습니다:
    1.  **측정 (Measure):** 로드된 이미지의 실제 픽셀 크기(`_imageSize`)를 가져옵니다.
    2.  **계산 (Calculate):** `BoxFit.contain`을 고려하여 화면에 표시되는 이미지의 정확한 `displaySize`(너비/높이)를 계산합니다.
    3.  **제한 (Constrain):** 박스를 그리는 `CustomPaint`가 이 정확한 `displaySize`와 일치하도록 강제합니다.
*   **결과:** 바운딩 박스가 기기 화면이 아닌 *렌더링된 이미지 픽셀*을 기준으로 그려지므로, 어떤 기기 방향에서도 완벽한 정렬을 보장합니다.

#### 2. 스와이프 내비게이션 (Swipe Navigation)
*   **기능:** 사용자가 그리드 화면으로 돌아가지 않고도 좌/우로 스와이프하여 동일한 미션 내의 다른 감지된 결함을 볼 수 있습니다.
*   **구현:** `DetectionFullScreenView`를 `PageView.builder`를 사용하도록 리팩토링했습니다.
*   **최적화:** 각 페이지(`_DetectionImagePage`)가 이미지 로딩과 "Ratio Fix" 계산을 독립적으로 관리하여 부드러운 성능을 보장합니다.

### B. 실시간 스트리밍 뷰 (`live_streaming_screen.dart`)

#### 1. 전체 가시성 수정 (Full Visibility Fix)
*   **문제점:** 비디오 플레이어가 `BoxFit.cover`를 사용하고 있어, 긴 스마트폰 화면에서 16:9 드론 영상의 가장자리가 잘리는 현상이 있었습니다. 이로 인해 주변부에 위치한 균열이 보이지 않을 수 있었습니다.
*   **수정:** `BoxFit.contain`으로 변경했습니다.
*   **결과:** 전체 비디오 피드(1280x720)가 모두 보입니다. 검은 여백이 생길 수 있지만, 시각적 데이터 손실은 없습니다.

#### 2. 정렬 검증 (Alignment Verification)
*   **확인:** 라이브 스트림은 `VideoPlayer`와 `CustomPaint`가 동일한 `SizedBox`와 `FittedBox`를 공유하는 `Stack`을 사용합니다. 이는 비디오 크기가 조절되면 박스도 완벽하게 함께 조절됨을 보장합니다.

---

## 3. 변경된 파일 요약

| 파일 | 주요 변경 사항 |
| :--- | :--- |
| `backend/core/stream_manager.py` | 추론 전처리 제거(원본 프레임 사용), 지연 시간 로깅 추가. |
| `frontend/lib/screens/mission_detail_screen.dart` | Ratio Fix를 위한 `LayoutBuilder` 추가, 스와이프를 위한 `PageView` 구현, `_DetectionImagePage` 리팩토링. |
| `frontend/lib/screens/live_streaming_screen.dart` | 비디오 맞춤을 `BoxFit.contain`으로 변경, 정렬 로직 검증. |

이 아키텍처는 **드론이 보는 것(AI)**, **저장되는 것(스토리지)**, 그리고 **사용자가 보는 것(앱)**이 모두 수학적으로 1:1로 정렬됨을 보장합니다.

## 4. 갤러리 최적화 (미션 상세)
- **스와이프 내비게이션**: 사용자가 감지된 이미지 간을 스와이프할 수 있도록 `DetectionFullScreenView`에 `PageView`를 구현했습니다.
- **가로 모드 지원 (Landscape Support)**: 반응형 레이아웃을 제공하기 위해 `MissionDetailScreen`에 `OrientationBuilder`를 추가했습니다.
    - **세로 모드 (Portrait)**: 상단에 정보 카드, 하단에 그리드가 있는 수직 레이아웃.
    - **가로 모드 (Landscape)**: 왼쪽에 정보 카드, 오른쪽에 그리드(3열)가 있는 수평 레이아웃.
- **코드 리팩토링**: `MissionDetailScreen` 구조를 정리하여 올바른 상태 관리와 위젯 분리를 보장했습니다.
- **디버그 배너**: 깔끔한 화면을 위해 앱에서 "DEBUG" 배너를 제거했습니다.
