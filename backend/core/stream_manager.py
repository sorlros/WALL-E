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
        self.rtmp_url = os.getenv("RTMP_URL", "rtmp://localhost:1935/live/test")
        # If rtmp_url is a digit string (e.g. "0"), convert to int for webcam index
        if isinstance(self.rtmp_url, str) and self.rtmp_url.isdigit():
            self.rtmp_url = int(self.rtmp_url)
        
        # Initialize YOLO model
        logger.info("Loading YOLO11n model...")
        self.model = YOLO("yolo11n.pt")
        logger.info("YOLO11n model loaded.")

        self.cap = None
        self.is_running = False
        
        # Threading support
        self.thread = None
        self.lock = threading.Lock()
        self.current_frame = None
        self.last_frame_time = 0
        
        # Mission & Detection Logic
        self.active_mission_id = None
        self.last_save_time = 0
        self.save_cooldown = 2.0  # Save detection at most once every 2 seconds

    def start(self):
        """Request the capture thread to start."""
        if self.is_running:
            return True

        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"Stream thread started for URL: {self.rtmp_url}")
        return True

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
        
        frame_interval = 3  # Run AI every 3 frames
        frame_count = 0
        
        # Cache for the last detection results (bounding boxes)
        last_results = None 
        
        while self.is_running:
            # Reconnect logic
            if self.cap is None or not self.cap.isOpened():
                try:
                    logger.info(f"Connecting to stream: {self.rtmp_url}")
                    self.cap = cv2.VideoCapture(self.rtmp_url)
                    if not self.cap.isOpened():
                        logger.error(f"Failed to open stream. Retrying in 2s...")
                        time.sleep(2)
                        continue
                    
                    # Buffer size optimization for low latency
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    logger.info("Stream connected successfully.")
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
                
                # 1. Preprocess every frame (needed for consistent display size)
                processed_frame = self._preprocess_frame(frame)

                # 2. Inference (Interval Check)
                if frame_count % frame_interval == 0:
                    # Run YOLOv8
                    results = self.model(processed_frame, conf=0.5, verbose=False)
                    if results:
                        last_results = results[0] # Cache the result
                        
                        # Auto-Save Logic
                        # If mission is active and confidence is high, save to DB
                        if self.active_mission_id:
                            boxes = results[0].boxes
                            if boxes:
                                best_conf = float(boxes.conf[0]) # Tensor to float
                                best_cls = int(boxes.cls[0])
                                label = results[0].names[best_cls]
                                
                                # Get Bounding Box [x, y, w, h] (normalized) for DB
                                # xywhn = Center X, Center Y, Width, Height (Normalized)
                                bbox_norm = boxes.xywhn[0].tolist() # [x, y, w, h]
                                
                                current_time = time.time()
                                if best_conf > 0.6 and (current_time - self.last_save_time > self.save_cooldown):
                                    self._save_detection(frame, label, best_conf, bbox_norm)
                                    self.last_save_time = current_time
                
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

    def _save_detection(self, frame, label, confidence, bbox):
        """Save the detected frame to disk and database."""
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
            cv2.imwrite(filepath, frame)
            
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
            
            logger.info(f"Auto-saved detection: {label} ({confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to save detection: {e}")
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
