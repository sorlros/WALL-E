from ultralytics import YOLO
import os

def train_best_model():
    # 1. 모델 로드
    model = YOLO('yolo11n.pt')

    # 2. 데이터셋 경로 설정 (Colab 환경 기준)
    # v4 데이터셋 (1:2 비율) 사용
    data_path = './datasets/planned_v4/data.yaml'
    
    if not os.path.exists(data_path):
        print(f"Error: Dataset not found at {data_path}")
        print("Please unzip planned_v4.zip to ./datasets/ first.")
        return

    print("🚀 Starting reproduction of BEST MODEL (v5)...")
    print("Key Configuration: imgsz=640, Dataset=v4 (1:2 ratio)")

    # 3. 학습 시작
    results = model.train(
        data=data_path,
        epochs=50,
        imgsz=640,        # 핵심: 512가 아닌 640 사용!
        batch=16,
        name='v5_best_repro',
        device=0,         # GPU 사용
        patience=10,
        save=True,
        verbose=True,
        
        # 증강 옵션 제어 (User Code 기준)
        mosaic=0.0,       # Mosaic 끄기 (균열 끊김 방지)
        mixup=0.0,        # Mixup 끄기 (Ghost 방지)
        hsv_h=0.0,        # 색상 변조 끄기
        hsv_s=0.0,
        hsv_v=0.0,
        translate=0.0,    # 이동 끄기 (Albumentations에서 이미 함)
        scale=0.0,        # 스케일 끄기
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.0,
        
        # 나머지 기본값(warmup 등)은 유지
    )
    
    print("Training Completed. Check runs/detect/v5_best_repro for results.")

if __name__ == "__main__":
    train_best_model()
