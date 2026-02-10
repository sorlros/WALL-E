import cv2
import time
import os
import threading
from dotenv import load_dotenv
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
        self.rtmp_url = os.getenv("RTMP_URL", 0)
        # If rtmp_url is a digit string (e.g. "0"), convert to int for webcam index
        if isinstance(self.rtmp_url, str) and self.rtmp_url.isdigit():
            self.rtmp_url = int(self.rtmp_url)
        
        # Initialize YOLO model
        # Using 'yolov8n.pt' (nano) for speed. Can be changed to custom trained model later.
        logger.info("Loading YOLOv8 model...")
        self.model = YOLO("yolov8n.pt")
        logger.info("YOLOv8 model loaded.")

        self.cap = None
        self.is_running = False
        
        # Threading support
        self.thread = None
        self.lock = threading.Lock()
        self.current_frame = None
        self.last_frame_time = 0

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
        """Background thread to handle connection and reading frames."""
        logger.info("Starting capture loop...")
        
        frame_interval = 3  # Process every 3rd frame
        frame_count = 0
        last_annotated_frame = None

        while self.is_running:
            # If no capture object or not opened, try to connect
            if self.cap is None or not self.cap.isOpened():
                try:
                    logger.info(f"Connecting to stream: {self.rtmp_url}")
                    self.cap = cv2.VideoCapture(self.rtmp_url)
                    
                    if not self.cap.isOpened():
                        logger.error(f"Failed to open stream at {self.rtmp_url}. Retrying in 2s...")
                        time.sleep(2)
                        continue
                    
                    # Connection successful
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    logger.info("Stream connected successfully.")
                    
                except Exception as e:
                    logger.error(f"Error connecting to stream: {e}")
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
                
                # Check if we should run inference
                if frame_count % frame_interval == 0:
                    # 1. Preprocess
                    processed_frame = self._preprocess_frame(frame)

                    # 2. Inference: Run YOLOv8 on the frame
                    # conf=0.5: Confidence threshold
                    results = self.model(processed_frame, conf=0.5, verbose=False) 
                    
                    # 3. Post-process: Plot results on the frame
                    # plot() returns a BGR numpy array
                    last_annotated_frame = results[0].plot()
                
                # If we skipped inference, we still want to show something.
                # Ideally, we should overlay the *last known detections* on the *current* frame.
                # However, since objects move, simple overlay might be misaligned.
                # For high FPS streams, just showing the last *processed* frame (stuttery video) 
                # or showing the *current raw* frame (smooth video, low FPS detections) are options.
                # Option A: Show current raw frame (no boxes) -> Bad UX (flickering boxes)
                # Option B: Show last annotated frame -> Video looks lower FPS but consistent
                # Option C: Draw last known boxes on current frame -> Best UX if implemented correctly.
                
                # For simplicity and "visual continuity" of the DETECTION result, 
                # let's stick with Option B (repeating last annotated frame) 
                # OR return the current frame if we want smooth video but choppy detections.
                
                # Let's go with a hybrid: 
                # The user asked for optimization. Processing every 3 frames means 30fps input -> 10fps inference.
                # If we just return 'last_annotated_frame', the video will look like 10fps.
                # If we want 30fps video with 10fps boxes, we need to save the boxes and draw them on current frame.
                
                # Given "Optimize", usually means reducing load. 
                # Let's use the 'last_annotated_frame' if available, otherwise current frame.
                # But to keep it simple and safe:
                
                final_output = last_annotated_frame if last_annotated_frame is not None else frame

                # Success: Encode and store
                ret, buffer = cv2.imencode('.jpg', final_output)
                if ret:
                    with self.lock:
                        self.current_frame = buffer.tobytes()
                        self.last_frame_time = time.time()
                
            except Exception as e:
                logger.error(f"Error during frame capture: {e}")
                if self.cap:
                    self.cap.release()
                self.cap = None
                time.sleep(1)

        # Cleanup on exit
        if self.cap:
            self.cap.release()
        logger.info("Capture loop ended.")

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
                # Wait slightly less than frame duration (e.g. for 30fps ~0.033)
                # But to ensure low latency, we yield as fast as possible if new frame?
                # For simplicity, sleep small amount to avoid busy loop
                time.sleep(0.01) 
            else:
                # If no frame, sleep longer to wait for connection
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
