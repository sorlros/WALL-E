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

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", ".env")
load_dotenv(dotenv_path=dotenv_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self):
        self.rtmp_url = os.getenv("RTMP_URL", "rtmp://1.238.76.151:1935/live/drone")
        # If rtmp_url is a digit string (e.g. "0"), convert to int for webcam index
        if isinstance(self.rtmp_url, str) and self.rtmp_url.isdigit():
            self.rtmp_url = int(self.rtmp_url)
        
        # Initialize YOLO model
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # Wall-E root
        # Actually line 15 implies 3 dirnames go to Wall-E root.
        # But let's look at line 15: os.path.join(..., "backend", ".env")
        # If I want backend/ml_models, I should use the backend root.
        
        # Let's verify:
        # __file__ = backend/core/stream_manager.py
        # dirname 1 = backend/core
        # dirname 2 = backend
        
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(backend_root)
        model_path = os.path.join(project_root, "runs", "detect", "wall-e-crack-detection", "v3_mixed_original2", "weights", "best.pt")
        
        logger.info(f"Loading Crack Detection Model from {model_path}...")
        self.model = YOLO(model_path)
        logger.info(f"Crack Detection Model loaded. Classes: {self.model.names}")

        self.cap = None
        self.is_running = False
        
        # Threading support
        self.thread = None
        self.lock = threading.Lock()
        self.current_frame = None
        self.last_frame_time = 0
        
        # Mission & Detection Logic
        # self.active_mission_id = None
        # self.last_save_time = 0
        self.active_mission_id = None
        self.last_save_time = 0
        self.save_cooldown = 2.0  # Save detection at most once every 2 seconds
        self._processed_track_ids = set() # Store track_ids that have been saved to DB
        
        # Callback for real-time updates (e.g. WebSocket)
        self.on_detection = None

    def set_callback(self, callback):
        """Set a callback function to be called on new detections."""
        self.on_detection = callback

    def start(self):
        """Request the capture thread to start."""
        if self.is_running:
            return True

        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"Stream thread started for URL: {self.rtmp_url}")
        return True

    def start_mission(self, mission_id):
        """Start a new mission and reset tracking state."""
        self.active_mission_id = mission_id
        self._processed_track_ids.clear()
        logger.info(f"Started mission {mission_id}. Tracking IDs reset.")
        self.start() # Ensure stream is running

    def stop_mission(self):
        """Stop the current active mission."""
        self.active_mission_id = None
        logger.info("Mission stopped.")


    def _preprocess_frame(self, frame, target_size=(640, 640)):
        """
        Preprocess logic:
        1. Resize while maintaining aspect ratio (Letterboxing)
        2. Pad the rest with gray color to match target_size
        """
        h, w = frame.shape[:2]
        ash, asw = target_size

        # Calculate scale to fit within target_size
        scale = min(ash / h, asw / w)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # Resize
        resized = cv2.resize(frame, (new_w, new_h))
        
        # Create a gray canvas
        canvas = np.full((ash, asw, 3), 114, dtype=np.uint8)
        
        # Center the image on the canvas
        top = (ash - new_h) // 2
        left = (asw - new_w) // 2
        
        canvas[top:top+new_h, left:left+new_w] = resized
        return canvas

    def _capture_loop(self):
        """Background thread to handle connection, reading frames, and AI inference."""
        logger.info("Starting capture loop...")
        
        frame_interval = 6  # Run AI every 6 frames (Optimized for 60 FPS Pass-through)
        frame_count = 0
        
        # Cache for the last detection results (bounding boxes)
        last_results = None 
        
        # Performance Profiling Variables
        fps_start_time = time.time()
        
        while self.is_running:
            # Reconnect logic
            if self.cap is None or not self.cap.isOpened():
                try:
                    logger.info(f"Connecting to stream: {self.rtmp_url}")
                    # Revert to the original working method for this specific environment
                    if isinstance(self.rtmp_url, str):
                        self.cap = cv2.VideoCapture(self.rtmp_url)
                    else:
                        self.cap = cv2.VideoCapture(self.rtmp_url)
                        
                    if not self.cap.isOpened():
                        logger.error(f"Failed to open stream. Retrying in 2s...")
                        time.sleep(2)
                        continue
                    
                    # Request specific resolution and FPS (1920x1080 @ 60fps)
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                    self.cap.set(cv2.CAP_PROP_FPS, 60)

                    # Buffer size optimization for low latency
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    logger.info("Stream connected successfully.")
                    
                    # Reset FPS timer on reconnect
                    fps_start_time = time.time()
                    frame_count = 0
                except Exception as e:
                    logger.error(f"Error connecting: {e}")
                    time.sleep(2)
                    continue

            # Read frame
            try:
                success, frame = self.cap.read()
                if not success:
                    logger.warning("Failed to read frame. Reconnecting...")
                    self.cap.release()
                    self.cap = None
                    time.sleep(1)
                    continue
                
                frame_count += 1
                
                # 1. Preprocess: removed to ensure correct bbox mapping for saved images
                # processed_frame = self._preprocess_frame(frame)
                processed_frame = frame 

                # 2. Inference (Interval Check)
                if frame_count % frame_interval == 0:
                    # Run YOLO11n with Tracking
                    # persist=True is crucial for keeping IDs across frames
                    start_time = time.time()
                    results = self.model.track(processed_frame, conf=0.6, persist=True, verbose=False)
                    detection_time = time.time()
                    inference_ms = (detection_time - start_time) * 1000
                    
                    # Performance Profiling (Every 60 frames)
                    if frame_count % 60 == 0:
                        elapsed = time.time() - fps_start_time
                        actual_fps = 60 / elapsed if elapsed > 0 else 0
                        
                        # Get YOLO inference time from results if available, else approximate
                        yolo_speed = results[0].speed['inference'] if results else inference_ms
                        
                        logger.info(f"📊 [성능 지표] 입력 해상도: {frame.shape[1]}x{frame.shape[0]} | 실제 스트리밍 FPS: {actual_fps:.2f} | YOLO 추론 속도: {yolo_speed:.1f}ms")
                        fps_start_time = time.time()

                    if results and results[0].boxes:
                        last_results = results[0] # Cache the result
                        boxes = results[0].boxes
                        
                        # Auto-Save Logic (Loop through ALL detections)
                        if self.active_mission_id:
                            # Iterate over each box to check track_id
                            # boxes.id is None if no tracks found
                            if boxes.id is not None:
                                track_ids = boxes.id.int().cpu().tolist()
                                confs = boxes.conf.cpu().tolist()
                                clss = boxes.cls.int().cpu().tolist()
                                xywhns = boxes.xywhn.cpu().tolist()
                                
                                for i, track_id in enumerate(track_ids):
                                    conf = confs[i]
                                    cls = clss[i]
                                    bbox_norm = xywhns[i]
                                    label = results[0].names[cls]
                                    
                                    # Unique Check: Only save if ID is NEW and Confidence is High
                                    if track_id not in self._processed_track_ids:
                                        if conf > 0.7:
                                            # Save!
                                            self._save_detection(frame, label, conf, bbox_norm, detection_time)
                                            self._processed_track_ids.add(track_id)
                                            logger.info(f"🆕 [Tracking] New Object ID {track_id} Saved! ({label}, {conf:.2f})")
                                        else:
                                            # Low confidence, but new ID. Wait for better frame?
                                            # For now, we simple ignore. If it gets better later, ID is same? 
                                            # Actually, if we don't save now, track_id is NOT added. 
                                            # So if next frame it is 0.8, it WILL be saved.
                                            pass
                                    else:
                                        # Already processed this ID
                                        pass
                            else:
                                # Fallback if no IDs (tracking failed but detection worked?)
                                pass
                                    
                        # Real-time WebSocket Logic (Send BEST detection for UI)
                        # We just send the first one (highest conf) for simple UI
                        if self.on_detection and boxes:
                            best_idx = 0 # YOLO sorts by conf? usually.
                            
                            track_id = int(boxes.id[best_idx]) if boxes.id is not None else None
                            conf = float(boxes.conf[best_idx])
                            cls = int(boxes.cls[best_idx])
                            label = results[0].names[cls]
                            bbox_norm = boxes.xywhn[best_idx].tolist()
                            
                            total_detections = len(boxes)
                            # Logs can be noisy, maybe reduce log level or frequency
                            # logger.info(f"⚡ ...")

                            detection_data = {
                                "label": label,
                                "confidence": conf,
                                "bbox": bbox_norm,
                                "timestamp": time.time(),
                                "count": total_detections, 
                                "saved_count": len(self._processed_track_ids), # Cumulative saved count
                                "track_id": track_id,
                                "detection_id": None # We don't track DB ID for stream updates usually
                            }
                            if self.on_detection:
                                self.on_detection(detection_data)
                
                # 3. Post-process: Overlay cached results on CURRENT frame
                final_output = processed_frame # Start with current raw frame
                
                if last_results is not None:
                    # Draw fresh boxes on the FRESH frame
                    final_output = last_results.plot(img=processed_frame)
                
                # 4. Low Latency Encoding
                # Quality 70 is a good balance for speed/size
                ret, buffer = cv2.imencode('.jpg', final_output, [cv2.IMWRITE_JPEG_QUALITY, 70])
                
                if ret:
                    with self.lock:
                        self.current_frame = buffer.tobytes()
                        self.last_frame_time = time.time()
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                if self.cap:
                    self.cap.release()
                self.cap = None
                time.sleep(1)

        if self.cap:
            self.cap.release()
        logger.info("Capture loop ended.")

    def _save_detection(self, frame, label, confidence, bbox, detection_timestamp=None):
        """Save the detected frame to disk and database. Measure latency."""
        try:
            db = SessionLocal()
            
            # 1. Create directory based on date (Local Cache / Fallback)
            # Ideally this uploads to Supabase Storage directly.
            today = datetime.now().strftime("%Y-%m-%d")
            save_dir = os.path.join("storage/images", today)
            os.makedirs(save_dir, exist_ok=True)
            
            # 2. Generate filename
            import uuid
            filename = f"{uuid.uuid4()}.jpg"
            filepath = os.path.join(save_dir, filename)
            
            # 3. Save Image (Original, Raw frame for better analysis)
            save_start = time.time()
            cv2.imwrite(filepath, frame)
            save_end = time.time()
            
            if detection_timestamp:
                latency_ms = (save_end - detection_timestamp) * 1000
                logger.info(f"⏱️ [Latency] Detection to Save: {latency_ms:.1f}ms (Write took {(save_end - save_start)*1000:.1f}ms)")
            
            # 4. Save to DB
            # Use public URL format for Supabase Storage
            image_url = f"/storage/images/{today}/{filename}"
            
            detection = models.Detection(
                mission_id=self.active_mission_id,
                image_url=image_url,
                label=label,
                confidence=float(confidence),
                bbox=bbox, 
                # GPS will be updated later via API or separate logic
            )
            db.add(detection)
            db.commit()
            db.refresh(detection)
            
            logger.info(f"Auto-saved detection: {label} ({confidence:.2f}) ID: {detection.id}")
            return detection
            
        except Exception as e:
            logger.error(f"Failed to save detection: {e}")
            return None
        finally:
            db.close()

    def get_frame(self):
        """
        Returns the latest available frame as JPEG bytes.
        Non-blocking. Returns None if no frame is available yet.
        """
        if not self.is_running:
            self.start()
        
        with self.lock:
            if self.current_frame:
                return self.current_frame
        
        return None

    def generate_frames(self):
        """Generator function for StreamingResponse"""
        while True:
            frame_bytes = self.get_frame()
            
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(0.01) 
            else:
                time.sleep(0.1)

    def release(self):
        """Stop the thread and release resources."""
        logger.info("Stopping stream manager...")
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self.thread = None
        logger.info("Stream manager stopped.")

# Global instance
stream_manager = StreamManager()
