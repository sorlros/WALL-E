# 오늘 작업 내역 요약 (Walkthrough)

## 1. 프로필 화면 레이아웃 (Profile Screen Layout) 개선
가로(Landscape) 모드 전환 시 발생하던 UI/UX 문제 및 아이콘 정렬 문제를 해결했습니다.

### 주요 수정 사항:
- **계정 정보(Account Information) 섹션 중앙 정렬**: 기기가 가로 방향일 때 "이메일(Email)"과 "이름(Name)" 세부 정보가 화면 중앙에 위치하도록 조정어 레이아웃이 깨지지 않게 보완했습니다.
- **아이콘 정렬 및 크기 조정**: "이메일"과 "이름" 앞의 아이콘들이 수직으로 올바르게 정렬되도록 간격을 맞추고 시인성 개선을 위해 아이콘 크기를 10 픽셀씩 늘렸습니다.

---

## 2. 모든 캡처 및 스트리밍에서 창문 블러(Privacy Blur) 적용 오류 수정
이전에 저장된 이미지(크랙 자동 검출)와 수동 캡처, 모바일로 전송되는 실시간 스트리밍 비디오에서 창문 영역에 블러(Blur)가 누락되는 문제를 해결했습니다.

### 이슈 원인:
기존에는 리소스(MacBook CPU)를 아끼기 위해 **3프레임에 한 번씩만** 창문을 탐지하고 해당 프레임에만 블러를 적용했습니다. 그러나 실제로 이미지를 저장(`_save_detection`), 수동 캡처(`manual_capture`), 모바일 스트리밍(`generate_frames`)할 때는 원본 프레임을 가져다 썼기 때문에, 블러가 없는 프레임이 수집되는 상황이 발생했습니다.

### 주요 수정 사항:
`backend/core/stream_manager_ai_only.py` 파일의 추론 루프(`_inference_loop`)와 캡처/스트리밍 출력 부분을 수정했습니다.

```diff
-  self._apply_window_blur(frame_to_infer, window_bboxes_list)
+  self.last_window_bboxes = window_bboxes_list # 바운딩 박스 캐싱
+
+  if self.last_window_bboxes: # 모든 프레임에 캐싱된 박스를 이용해 블러 적용
+      self._apply_window_blur(frame_to_infer, self.last_window_bboxes)
```

- **바운딩 박스 캐싱**: `StreamManager` 클래스에 `self.last_window_bboxes` 변수를 추가하여, 3프레임마다 인식된 가장 최신의 창문 영역 위치(Bounding Box)를 저장(Cache)합니다.
- **자동 저장 (Auto-save) 보안 필터**: 매 프레임마다 모델이 추론을 시작할 때, 이전 프레임에서 가져온 창문 영역 캐시를 바탕으로 원본 입력 이미지에 블러를 강제로 적용합니다. 이를 통해 크랙이 감지되어 자동 저장이 일어날 때 무조건 블러가 들어갑니다.
- **수동 캡처 (Manual Capture) 보완**: 수동 캡처(API 호출 시)를 위해 복사해 둔 화면 이미지에도 마찬가지로 블러 처리(`_apply_window_blur`) 필터를 덧입힌 뒤 저장되게 변경했습니다.
- **라이브 스트리밍 (Live Streaming) 송출 개선**: 모바일 단말기로 전달되는 화면 스트림 스레드(`generate_frames`)에서도 클라이언트에 인코딩된 프레임을 전달하기 전에 실시간으로 블러를 적용했습니다.

### 검증 방법 (Verification)
- 백엔드 서버 구동 후 모바일 앱(혹은 프론트엔드 URL)에서 라이브 스트리밍을 볼 때 프레임이 깨지지 않고 창문 모자이크가 끊김 없이 적용되는지 확인
- 크랙 감지 이력(Gallery Screen 등)과 수동 캡처 항목 확인 시 100% 창문 쪽이 가려져 있는지 확인
