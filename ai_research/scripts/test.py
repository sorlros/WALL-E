import os
import cv2
from ultralytics import YOLO
from pathlib import Path
from tqdm import tqdm

def run_inference_on_videos(model_path, data_dir, output_dir):
    """
    실전 영상 데이터(datasets/real_data)에 대해 추론을 수행하고 결과를 저장합니다.
    """
    # 1. 모델 로드
    if not os.path.exists(model_path):
        print(f"Error: 모델 파일을 찾을 수 없습니다: {model_path}")
        return

    model = YOLO(model_path)
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. 영상 파일 목록 가져오기 (mp4, avi 등)
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv']
    video_files = []
    for ext in video_extensions:
        video_files.extend(list(data_dir.glob(ext)))

    if not video_files:
        print(f"No video files found in {data_dir}")
        return

    print(f"Found {len(video_files)} videos for inference.")

    # 3. 영상별 추론 수행
    for video_path in video_files:
        print(f"\nProcessing: {video_path.name}")
        
        # YOLO의 .predict() 기능을 사용하여 영상 추론 수행
        # save=True: 결과 영상 저장
        # imgsz=640: 학습 환경과 동일한 해상도
        # conf=0.25: 탐지 임계값 (결과가 너무 안 나오면 0.1 등으로 조절 가능)
        results = model.predict(
            source=str(video_path),
            project=str(output_dir),
            name=video_path.stem,
            save=True,
            imgsz=640,
            conf=0.25,
            device='0' if os.environ.get('CUDA_VISIBLE_DEVICES') else 'cpu'
        )
        
        print(f"Done: {video_path.name} -> Result saved in {output_dir}/{video_path.stem}")

if __name__ == "__main__":
    # 프로젝트 루트 경로 설정
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # 🎯 [수정 필요] 학습된 가중치 파일 경로 (예: 'best.pt' 또는 'runs/detect/train/weights/best.pt')
    # 만약 아직 학습 전이라면 'yolo11s.pt'를 넣어 테스트해볼 수 있습니다.
    MODEL_WEIGHTS = Path(__file__).parent / "best.pt"
    
    # 만약 위 경로에 파일이 없다면 현재 디렉토리의 모델이나 기본 모델 시도
    if not MODEL_WEIGHTS.exists():
        MODEL_WEIGHTS = "yolo11s.pt"
        print(f"Warning: 학습된 가중질를 찾지 못해 기본 모델({MODEL_WEIGHTS})을 사용합니다.")

    VIDEO_DIR = BASE_DIR / "datasets" / "real_data"
    OUTPUT_DIR = BASE_DIR / "ai_research" / "inference_results"

    run_inference_on_videos(MODEL_WEIGHTS, VIDEO_DIR, OUTPUT_DIR)
