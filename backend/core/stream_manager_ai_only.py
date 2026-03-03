import cv2
import time
import os
import threading
from dotenv import load_dotenv
# Database imports
from db import models, schemas
from db.database import SessionLocal
from datetime import datetime
import logging
import numpy as np
from ultralytics import YOLO
from core.reid_manager import ReIDManager

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", ".env")
load_dotenv(dotenv_path=dotenv_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self):
        self.rtmp_url = os.getenv("RTMP_URL", "rtmp://1.238.76.151:1935/live/drone")
        if isinstance(self.rtmp_url, str) and self.rtmp_url.isdigit():
            self.rtmp_url = int(self.rtmp_url)
        
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(backend_root)
        # model_path = os.path.join(project_root, "runs", "detect", "wall-e-crack-detection", "v3_mixed_original", "weights", "best.pt")
        model_path = os.path.join(project_root, "runs", "detect", "crack-with-background", "0224_last_model.pt")
        # model_path = os.path.join(project_root, "runs", "detect", "crack-with-background", "0224_last_model.pt")
        
        logger.info(f"Loading Crack Detection Model from {model_path}...")
        self.model = YOLO(model_path)
        logger.info(f"Crack Detection Model loaded. Classes: {self.model.names}")

        window_model_path = os.path.join(project_root, "runs", "detect", "window", "window-model.pt")
        logger.info(f"Loading Window Detection Model from {window_model_path}...")
        self.window_model = YOLO(window_model_path)
        logger.info(f"Window Detection Model loaded. Classes: {self.window_model.names}")

        self.cap = None
        self.is_running = False
        
        # Threading mechanisms
        self.camera_thread = None
        self.inference_thread = None
        
        self.frame_lock = threading.Lock()
        self.latest_frame = None
        
        self.results_lock = threading.Lock()
        self.latest_results = None
        
        # Cache for window blur
        self.last_window_bboxes = []
        
        # Mission & Detection Logic
        self.active_mission_id = None
        self.saved_crack_count = 0
        self.last_save_time = 0
        self.save_cooldown = 2.0
        
        # Initialize ReIDManager for duplicate filtering
        # Lowered threshold to 0.80 for more aggressive filtering of duplicates during movement
        self.reid_manager = ReIDManager(threshold=0.80, max_cache_size=50)
        
        # Callback for real-time updates (e.g. WebSocket)
        self.on_detection = None

    def set_callback(self, callback):
        self.on_detection = callback

    def start(self):
        """Start the background threads."""
        if self.is_running:
            return True

        self.is_running = True
        self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
        
        self.camera_thread.start()
        self.inference_thread.start()
        
        logger.info(f"Stream threads started for URL: {self.rtmp_url}")
        return True

    def start_mission(self, mission_id):
        self.active_mission_id = mission_id
        # Clear ReID cache for the new mission
        self.reid_manager.clear_mission_cache(mission_id)
        self.saved_crack_count = 0
        logger.info(f"Started mission {mission_id}. Re-ID cache reset.")
        self.start()

    def stop_mission(self):
        self.active_mission_id = None
        logger.info("Mission stopped.")

    def _camera_loop(self):
        """Thread 1: Dedicated to reading frames from the camera as fast as possible to prevent buffer lag."""
        logger.info("Starting camera thread...")
        
        while self.is_running:
            if self.cap is None or not self.cap.isOpened():
                try:
                    logger.info(f"Connecting to stream: {self.rtmp_url}")
                    self.cap = cv2.VideoCapture(self.rtmp_url)
                    
                    if not self.cap.isOpened():
                        logger.error(f"Failed to open stream. Retrying in 2s...")
                        time.sleep(2)
                        continue
                    
                    # Request specific resolution and FPS (1920x1080 @ 60fps)
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                    self.cap.set(cv2.CAP_PROP_FPS, 60)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Low latency requirement
                    logger.info("Stream connected successfully.")
                    
                except Exception as e:
                    logger.error(f"Error connecting: {e}")
                    time.sleep(2)
                    continue

            try:
                success, frame = self.cap.read()
                if not success:
                    logger.warning("Failed to read frame. Reconnecting...")
                    self.cap.release()
                    self.cap = None
                    time.sleep(1)
                    continue
                
                # Update the latest frame with zero blocking operations
                with self.frame_lock:
                    self.latest_frame = frame
                
            except Exception as e:
                logger.error(f"Error in camera loop: {e}")
                if self.cap:
                    self.cap.release()
                self.cap = None
                time.sleep(1)

        if self.cap:
            self.cap.release()
        logger.info("Camera thread ended.")

    def _apply_window_blur(self, frame, window_boxes):
        """Applies a strong Gaussian blur to the regions of the frame containing windows."""
        h, w = frame.shape[:2]
        for box in window_boxes:
            # Extract normalized coordinates
            cx, cy, bw, bh = box['bbox_norm']
            
            # Convert to pixel coordinates
            x1 = int((cx - bw / 2) * w)
            y1 = int((cy - bh / 2) * h)
            x2 = int((cx + bw / 2) * w)
            y2 = int((cy + bh / 2) * h)
            
            # Ensure bounds are within image
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            # Skip if box is invalid (e.g. out of bounds or negative width/height)
            if x2 <= x1 or y2 <= y1:
                continue
                
            # Extract the ROI (Region of Interest)
            roi = frame[y1:y2, x1:x2]
            
            # Apply a heavy Gaussian blur. Kernel size must be odd and positive.
            # Using 51x51 for a strong blur effect on high-res images.
            if roi.size > 0:
                blurred_roi = cv2.GaussianBlur(roi, (99, 99), 30)
                frame[y1:y2, x1:x2] = blurred_roi
        return frame

    def _inference_loop(self):
        """Thread 2: Dedicated to running YOLO inference at its own pace (e.g. 20-30 FPS)."""
        logger.info("Starting inference thread...")
        
        inference_count = 0
        fps_start_time = time.time()
        
        while self.is_running:
            # 1. Grab the latest frame
            frame_to_infer = None
            with self.frame_lock:
                if self.latest_frame is not None:
                    frame_to_infer = self.latest_frame.copy()
            
            if frame_to_infer is None:
                time.sleep(0.01) # Wait for camera to warm up
                continue
                
            # 2. Run Inference
            start_time = time.time()
            results = self.model.track(frame_to_infer, conf=0.55, persist=True, verbose=False)
            inference_count += 1
            
            # --- Window Detection (Every 3 frames to save MacBook resources) ---
            if inference_count % 3 == 0:
                win_results = self.window_model.predict(frame_to_infer, conf=0.5, verbose=False)
                window_bboxes_list = []
                if win_results and len(win_results) > 0 and win_results[0].boxes:
                    win_boxes = win_results[0].boxes
                    for idx in range(len(win_boxes)):
                        window_bboxes_list.append({
                            "label": win_results[0].names[int(win_boxes.cls[idx])],
                            "confidence": float(win_boxes.conf[idx]),
                            "bbox": win_boxes.xywh[idx].tolist(), # xywh needed for UI drawing (or xywhn)
                            "bbox_norm": win_boxes.xywhn[idx].tolist()
                        })
                
                # Update cached window bboxes
                self.last_window_bboxes = window_bboxes_list
                
                # Send window bboxes via WebSocket asynchronously
                if self.on_detection:
                    self.on_detection({
                        "type": "window",
                        "bboxes": window_bboxes_list,
                        "timestamp": time.time()
                    })
                    
            # Apply privacy blur to the current inference frame (in-place modification)
            # This runs on every frame to ensure saved images and stream outputs are always blurred,
            # using the cached bboxes from the most recent window detection.
            if self.last_window_bboxes:
                self._apply_window_blur(frame_to_infer, self.last_window_bboxes)
            # -------------------------------------------------------------------
            
            # Profiling (Every 30 inferences)
            if inference_count % 30 == 0:
                elapsed = time.time() - fps_start_time
                actual_fps = 30 / elapsed if elapsed > 0 else 0
                yolo_speed = results[0].speed['inference'] if (results and results[0].speed) else 0
                logger.info(f"📊 [AI 스레드] 입력 해상도: {frame_to_infer.shape[1]}x{frame_to_infer.shape[0]} | 실제 AI FPS: {actual_fps:.2f} | YOLO 추론 속도: {yolo_speed:.1f}ms")
                fps_start_time = time.time()

            # 3. Process Results
            if results and len(results) > 0:
                # Update latest results for the streamer thread to draw
                with self.results_lock:
                    self.latest_results = results[0]
                    
                boxes = results[0].boxes
                if boxes:
                    # Keep track of the highest similarity found in this frame (for UI)
                    best_sim_for_ui = 0.0
                    best_matched_id_for_ui = None
                    
                    # Auto-Save Logic (Loop through ALL detections)
                    if self.active_mission_id:
                        if boxes.id is not None:
                            track_ids = boxes.id.int().cpu().tolist()
                            confs = boxes.conf.cpu().tolist()
                            clss = boxes.cls.int().cpu().tolist()
                            xywhns = boxes.xywhn.cpu().tolist()
                            
                            for i in range(len(boxes)):
                                conf = confs[i]
                                cls = clss[i]
                                bbox_norm = xywhns[i]
                                label = results[0].names[cls]
                                
                                # Use high confidence threshold for saving
                                if conf > 0.7:
                                    # 1. Convert normalized bbox to pixel coordinates for cropping
                                    h, w = frame_to_infer.shape[:2]
                                    cx, cy, bw, bh = bbox_norm
                                    
                                    # Expand the bounding box by 10% (margin) to capture more context for embedding
                                    # This helps MobileNetV3 identify the same crack even if the drone shifts slightly
                                    margin_w = bw * 0.10
                                    margin_h = bh * 0.10
                                    
                                    x1 = int((cx - (bw/2 + margin_w)) * w)
                                    y1 = int((cy - (bh/2 + margin_h)) * h)
                                    x2 = int((cx + (bw/2 + margin_w)) * w)
                                    y2 = int((cy + (bh/2 + margin_h)) * h)
                                    
                                    # Ensure bounds are within image
                                    x1, y1 = max(0, x1), max(0, y1)
                                    x2, y2 = min(w, x2), min(h, y2)
                                    
                                    # 2. Crop the detected object with margin
                                    crop_img = frame_to_infer[y1:y2, x1:x2]
                                    
                                    if crop_img.size > 0:
                                        # 3. Extract embedding using MobileNetV3
                                        embedding = self.reid_manager.get_embedding(crop_img)
                                        
                                        if embedding is not None:
                                            # 4. Check for duplicates (Pass frame_id and track_id for spatial/temporal filtering)
                                            current_track_id = track_ids[i]
                                            is_dup, max_sim, matched_id = self.reid_manager.is_duplicate(
                                                self.active_mission_id, 
                                                embedding, 
                                                frame_id=inference_count, 
                                                track_id=current_track_id
                                            )
                                            
                                            if is_dup:
                                                logger.info(f"🔄 [Re-ID Drop] Duplicate crack detected. Sim: {max_sim:.2f} >= Threshold. Matched ID: {matched_id}")
                                            else:
                                                # Not a duplicate, save it!
                                                detection = self._save_detection(frame_to_infer, label, conf, bbox_norm, start_time)
                                                if detection:
                                                    self.reid_manager.add_to_cache(
                                                        self.active_mission_id, 
                                                        detection.id, 
                                                        embedding,
                                                        frame_id=inference_count,
                                                        track_id=current_track_id
                                                    )
                                                    self.saved_crack_count += 1
                                                    logger.info(f"🆕 [Re-ID Saved] New unique crack! Sim was {max_sim:.2f}. ID: {detection.id}")
                                            
                                            # Update the highest similarity seen in this frame to be sent to UI
                                            if max_sim > best_sim_for_ui:
                                                best_sim_for_ui = max_sim
                                                best_matched_id_for_ui = matched_id

                    # Real-time WebSocket Logic (Send BEST detection for UI)
                    if self.on_detection:
                        best_idx = 0 
                        track_id = int(boxes.id[best_idx]) if boxes.id is not None else None
                        conf = float(boxes.conf[best_idx])
                        cls = int(boxes.cls[best_idx])
                        label = results[0].names[cls]
                        bbox_norm = boxes.xywhn[best_idx].tolist()
                        
                        detection_data = {
                            "type": "crack",
                            "label": label,
                            "confidence": conf,
                            "bbox": bbox_norm,
                            "timestamp": time.time(),
                            "count": len(boxes), 
                            "saved_count": self.saved_crack_count,
                            "track_id": track_id,
                            "detection_id": None,
                            "reid_sim": float(best_sim_for_ui),
                            "matched_id": best_matched_id_for_ui
                        }
                        self.on_detection(detection_data)
            else:
                 # No detections, clear the old boxes
                 with self.results_lock:
                     self.latest_results = None

    def _save_detection(self, frame, label, confidence, bbox, detection_timestamp=None, is_manual=False):
        try:
            db = SessionLocal()
            today = datetime.now().strftime("%Y-%m-%d")
            save_dir = os.path.join("storage/images", today)
            os.makedirs(save_dir, exist_ok=True)
            
            import uuid
            filename = f"{uuid.uuid4()}.jpg"
            filepath = os.path.join(save_dir, filename)
            
            save_start = time.time()
            cv2.imwrite(filepath, frame)
            save_end = time.time()
            
            if detection_timestamp:
                latency_ms = (save_end - detection_timestamp) * 1000
                logger.info(f"⏱️ [Latency] Detection to Save: {latency_ms:.1f}ms (Write took {(save_end - save_start)*1000:.1f}ms)")
            
            image_url = f"/storage/images/{today}/{filename}"
            
            detection = models.Detection(
                mission_id=self.active_mission_id,
                image_url=image_url,
                label=label,
                confidence=float(confidence),
                bbox=bbox,
                is_manual=is_manual # Set the manual flag
            )
            db.add(detection)
            db.commit()
            db.refresh(detection)
            
            logger.info(f"[{'MANUAL' if is_manual else 'AUTO'}] Saved detection: {label} ({confidence:.2f}) ID: {detection.id}")
            return detection
            
        except Exception as e:
            logger.error(f"Failed to save detection: {e}")
            return None
        finally:
            db.close()

    def manual_capture(self, mission_id: int):
        """Called via API to manually capture and save the current frame."""
        logger.info(f"📸 Manual capture requested for mission {mission_id}")
        
        frame_to_save = None
        with self.frame_lock:
            if self.latest_frame is not None:
                frame_to_save = self.latest_frame.copy()
                
        if frame_to_save is None:
            logger.warning("No frame available for manual capture.")
            return False, "No frame available"

        # Try to attach current tracking boxes if available
        results_to_draw = None
        with self.results_lock:
            results_to_draw = self.latest_results

        # We will save the RAW frame or the DRAWN frame?
        # Usually, users want to see what they clicked on. Let's draw the current boxes.
        final_output = frame_to_save
        if results_to_draw is not None:
            final_output = results_to_draw.plot(img=frame_to_save)
            
        # Apply privacy blur to manual captures
        if self.last_window_bboxes:
            self._apply_window_blur(final_output, self.last_window_bboxes)

        # Build a dummy bbox for the whole frame, or pass None if no specific box
        # Since this is a manual capture of the whole scene, bbox can be None or an empty list
        
        detection = self._save_detection(
            frame=final_output,
            label="manual",
            confidence=1.0,
            bbox=None,
            is_manual=True
        )
        
        if detection:
            return True, f"Image captured successfully. ID: {detection.id}"
        else:
            return False, "Failed to save image to DB"

    def generate_frames(self):
        """Thread 3 (FastAPI Route): Generator logic to encode and stream frames."""
        if not self.is_running:
            self.start()

        fps_start_time = time.time()
        stream_count = 0
        
        while True:
            # Throttle stream output loop to ~30 FPS to prevent mobile decoding overload and bandwidth saturation
            time.sleep(1/30.0)
            
            frame_to_encode = None
            with self.frame_lock:
                if self.latest_frame is not None:
                    # Don't deep copy here to save memory, just keep reference.
                    # We will create a fresh canvas if we draw boxes.
                    frame_to_encode = self.latest_frame.copy() 
            
            if frame_to_encode is None:
                continue

            results_to_draw = None
            with self.results_lock:
                results_to_draw = self.latest_results

            final_output = frame_to_encode
            if results_to_draw is not None:
                final_output = results_to_draw.plot(img=frame_to_encode)
            
            # Apply privacy blur to the stream
            if self.last_window_bboxes:
                self._apply_window_blur(final_output, self.last_window_bboxes)
            
            # [Optimization] Resize image before sending (1280x720) 
            # 1080p MJPEG stream at 60fps is too heavy for mobile WiFi and Flutter decoders.
            final_output = cv2.resize(final_output, (1280, 720))
            
            # [Optimization] Lower JPEG quality to 50 for mobile streaming bandwidth
            ret, buffer = cv2.imencode('.jpg', final_output, [cv2.IMWRITE_JPEG_QUALITY, 50])
            
            if ret:
                 frame_bytes = buffer.tobytes()
                 yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                 
                 stream_count += 1
                 if stream_count % 30 == 0:
                     elapsed = time.time() - fps_start_time
                     actual_fps = 30 / elapsed if elapsed > 0 else 0
                     logger.info(f"📡 [송출 스레드] 클라이언트 MJPEG 전송 FPS: {actual_fps:.2f} (720p, Q:50)")
                     fps_start_time = time.time()

    def release(self):
        logger.info("Stopping stream manager...")
        self.is_running = False
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=2.0)
        if self.inference_thread and self.inference_thread.is_alive():
            self.inference_thread.join(timeout=2.0)
        self.camera_thread = None
        self.inference_thread = None
        logger.info("Stream manager stopped.")

# Global instance
stream_manager = StreamManager()

