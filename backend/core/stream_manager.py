
import cv2
import time
import os
import threading
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self):
        self.rtmp_url = os.getenv("RTMP_URL", 0)
        # If rtmp_url is a digit string (e.g. "0"), convert to int for webcam index
        if isinstance(self.rtmp_url, str) and self.rtmp_url.isdigit():
            self.rtmp_url = int(self.rtmp_url)
        
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

    def _capture_loop(self):
        """Background thread to handle connection and reading frames."""
        logger.info("Starting capture loop...")
        
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
                
                # Success: Encode and store
                ret, buffer = cv2.imencode('.jpg', frame)
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
