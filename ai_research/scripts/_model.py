from ultralytics import YOLO
import os

def train_model():
    # 1. 모델 로드 (YOLOv11 Nano 버전을 기본으로 설정하여 속도 최적화)
    # n: nano, s: small, m: medium, l: large, x: extra large
    model = YOLO("yolo11n.pt") 

    # 2. 데이터셋 설정 파일 경로
    # 스크립트 파일의 위치를 기준으로 dataset/data.yaml을 찾습니다.
    # 이렇게 하면 어느 폴더에서 실행하든(재생 버튼 포함) 경로를 잘 찾습니다.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.normpath(os.path.join(script_dir, '..', 'dataset', 'data.yaml'))

    # 3. 학습 시작
    print(f"학습을 시작합니다... (데이터 설정: {data_path})")
    results = model.train(
        data=data_path,
        epochs=30,                 # 드론 시점의 복잡한 데이터를 배우기 위해 횟수 증가
        imgsz=640,                  # 입력해상도 (레터박스 자동 적용)
        batch=16,                   # GPU/CPU 성능에 따라 조절
        name='crack_detection_v2',  # 고도화 모델 이름 (v2)
        device='cpu',               # GPU 사용 시 '0'으로 변경 권장
        # --- 드론 시점 특화 데이터 증강 (Augmentation) ---
        perspective=0.0005,         # 원근 왜곡: 드론이 비스듬히 찍는 각도 재현
        degrees=15.0,               # 회전: 드론의 비행 방향 무관하게 탐지
        scale=0.5,                  # 배율: 드론 고도 변화(줌 인/아웃) 대응
        mosaic=1.0,                 # 모자이크: 여러 환경을 섞어 복합 상황 학습
        multi_scale=True            # 다중 스케일 학습: 다양한 크기의 균열 대응
    )
    
    print("학습이 완료되었습니다!")
    print(f"학습 결과는 'runs/detect/crack_detection_v1' 폴더에 저장됩니다.")

if __name__ == "__main__":
    train_model()
