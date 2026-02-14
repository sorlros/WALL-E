import cv2
from ultralytics import YOLO
from pathlib import Path
import time
import os

"""
Script: test_model.py
Purpose: 
1. Load 'models/best.pt'
2. Run inference on video files in 'ai_research/test_data'
3. Visually display the results with bounding boxes.
"""

def test_model_on_videos():
    # 1. Path Setup
    model_path = Path("models/best.pt")
    input_dir = Path("ai_research/test_data")
    
    if not model_path.exists():
        print(f"❌ Error: Model not found at {model_path}")
        return
        
    if not input_dir.exists():
        print(f"❌ Error: Input directory not found at {input_dir}")
        os.makedirs(input_dir, exist_ok=True)
        print(f"📂 Created {input_dir}. Please put some video files there.")
        return

    # 2. Load Model
    print(f"🚀 Loading model from {model_path}...")
    model = YOLO(model_path)

    # 3. Find Videos
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv']
    video_files = []
    for ext in video_extensions:
        video_files.extend(input_dir.glob(ext))
        
    if not video_files:
        print(f"⚠️ No video files found in {input_dir}. Add .mp4, .avi, .mov files.")
        return
        
    print(f"📂 Found {len(video_files)} videos to test.")

    # 4. Process Each Video
    for video_file in video_files:
        print(f"\n🎥 Testing: {video_file.name}")
        cap = cv2.VideoCapture(str(video_file))
        
        if not cap.isOpened():
            print(f"❌ Could not open video: {video_file.name}")
            continue
            
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"   Resolution: {width}x{height}, FPS: {fps}")
        print("   Press 'q' to skip to next video, 'ESC' to exit script.")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break # End of video
                
            start_time = time.time()
            
            # --- INFERENCE ---
            # stream=True is efficient for video loop
            # conf=0.25: Confidence threshold (adjust if needed)
            results = model.predict(frame, conf=0.25, verbose=False)
            
            # --- VISUALIZATION ---
            # plot() returns the frame with boxes drawn
            annotated_frame = results[0].plot()
            
            # Calculate FPS for display
            process_time = time.time() - start_time
            inference_fps = 1.0 / (process_time + 1e-6)
            
            cv2.putText(annotated_frame, f"Inference FPS: {inference_fps:.1f}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Show Result
            # Resize for display if video is huge (e.g. 4k)
            display_frame = annotated_frame
            if width > 1280:
                display_frame = cv2.resize(annotated_frame, (1280, int(1280 * height / width)))
                
            cv2.imshow(f"YOLO Test - {video_file.name}", display_frame)
            
            # Controls
            # Wait depending on FPS (e.g., 30ms for ~30fps)
            # Use 1ms for max speed, or adjust to sync with real-time
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'): # Skip current video
                break
            elif key == 27: # ESC: Exit script
                cap.release()
                cv2.destroyAllWindows()
                return

        cap.release()
        cv2.destroyAllWindows()
        print(f"✅ Finished: {video_file.name}")

if __name__ == "__main__":
    test_model_on_videos()
