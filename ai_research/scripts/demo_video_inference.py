import cv2
from ultralytics import YOLO
import os
import argparse

def run_video_inference(model_path, video_path, output_path, conf=0.25):
    # 0. 경로 확인
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return
    
    # 1. 모델 로드
    print(f"Loading model from {model_path}...")
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # 2. 비디오 캡처 객체 생성
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Processing Video: {width}x{height} @ {fps:.2f}fps ({total_frames} frames)")
    
    # 3. 비디오 저장 객체 생성
    # Mac/Linux 호환성을 위해 mp4v 코덱 사용
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    
    # 출력 경로 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    
    # 4. 프레임별 추론 루프
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # 추론 수행
        # imgsz=640: 학습 해상도와 일치시킴
        results = model.predict(frame, conf=conf, imgsz=640, verbose=False)
        
        # 결과 시각화 (이미지에 박스 그리기)
        annotated_frame = results[0].plot()
        
        # 결과 영상에 쓰기
        out.write(annotated_frame)
        
        frame_count += 1
        if frame_count % 30 == 0:
            print(f"Progress: {frame_count}/{total_frames} ({frame_count/total_frames*100:.1f}%)")
            
    # 5. 종료 및 자원 해제
    cap.release()
    out.release()
    print(f"\nInference Complete! Saved to: {output_path}")

if __name__ == "__main__":
    # 기본 설정
    DEFAULT_MODEL = "runs/detect/wall-e-crack-detection/v3_mixed_original2/weights/best.pt"
    # 영상 파일 이름에 공백이 있어서 주의 필요
    DEFAULT_VIDEO = "ai_research/test_data/TalkMedia_talkv_hevc.mp4.mp4"
    DEFAULT_OUTPUT = "ai_research/test_data/inference_result2.mp4"
    
    parser = argparse.ArgumentParser(description="Run YOLO inference on a video file")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Path to the trained model (.pt)")
    parser.add_argument("--video", type=str, default=DEFAULT_VIDEO, help="Path to the input video file")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT, help="Path to save the output video")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    
    args = parser.parse_args()
    
    run_video_inference(args.model, args.video, args.output, args.conf)
