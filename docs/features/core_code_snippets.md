# Wall-E 프로젝트 핵심 코드 (Core Code Snippets)

발표 자료에 사용하기 좋은 프로젝트의 핵심 기능 코드들을 선정했습니다.

---

## 1. 백엔드: 실시간 균열 감지 루프 (Inference Loop)
**위치**: `backend/core/stream_manager.py`
**설명**: RTMP 스트림에서 프레임을 가져와 YOLOv8 모델로 추론하고, 결과가 있으면 WebSocket으로 전송 및 DB에 자동 저장하는 핵심 로직입니다.

```python
# backend/core/stream_manager.py

    def _capture_loop(self):
        """배경 스레드에서 비디오 캡처 및 AI 추론 수행"""
        while self.is_running:
            # ... (프레임 읽기 생략) ...

            # 2. AI 추론 (3프레임마다 실행하여 성능 최적화)
            if frame_count % frame_interval == 0:
                results = self.model(processed_frame, conf=0.5, verbose=False)

                if results:
                    # 3. 자동 저장 (정확도 0.7 이상)
                    if self.active_mission_id:
                        if best_conf > 0.7 and (current_time - self.last_save_time > self.save_cooldown):
                            saved_detection = self._save_detection(frame, label, best_conf, bbox_norm)

                    # 4. 실시간 웹소켓 전송 (Confidence > 0.5)
                    if self.on_detection and results[0].boxes:
                        detection_data = {
                            "label": label,
                            "confidence": best_conf,
                            "bbox": bbox_norm, # [x, y, w, h] 정규화 좌표
                            "count": total_detections,
                            "timestamp": time.time()
                        }
                        self.on_detection(detection_data) # 콜백 호출
```

---

## 2. 백엔드: 웹소켓 데이터 브로드캐스팅 (WebSocket Broadcast)
**위치**: `backend/api/stream.py`
**설명**: `StreamManager`에서 감지된 데이터를 연결된 모든 클라이언트(앱)에게 실시간으로 전송하는 비동기 함수입니다.

```python
# backend/api/stream.py

# StreamManager로부터 데이터를 받는 콜백 함수
def detection_callback(data):
    if global_loop and global_loop.is_running():
        # 메인 스레드의 이벤트 루프를 통해 비동기 전송
        asyncio.run_coroutine_threadsafe(manager.broadcast(data), global_loop)

# 연결된 모든 클라이언트에게 데이터 전송
async def broadcast(self, message: dict):
    for connection in self.active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
```

---

## 3. 프론트엔드: 바운딩 박스 그리기 (Custom Painter)
**위치**: `frontend/lib/screens/live_streaming_screen.dart`
**설명**: WebSocket으로 받은 정규화된(0~1) 좌표 데이터를 실제 화면 픽셀 좌표로 변환하여 비디오 위에 박스를 그리는 UI 코드입니다.

```dart
// frontend/lib/screens/live_streaming_screen.dart

class BoundingBoxPainter extends CustomPainter {
  final List<dynamic> detections;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.red
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0;

    for (var detection in detections) {
      // bbox: [centerX, centerY, width, height] (Normalized 0.0 ~ 1.0)
      final bbox = detection['bbox']; 
      
      // 정규화 좌표를 실제 화면 픽셀 좌표로 변환
      final double left = (bbox[0] - bbox[2] / 2) * size.width;
      final double top = (bbox[1] - bbox[3] / 2) * size.height;
      final double width = bbox[2] * size.width;
      final double height = bbox[3] * size.height;

      // 박스 그리기
      canvas.drawRect(Rect.fromLTWH(left, top, width, height), paint);
      
      // 라벨 및 확률 텍스트 그리기
      // ... (TextPainter 코드) ...
    }
  }
}
```
