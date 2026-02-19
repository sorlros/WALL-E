# # GPU 유무 확인
# !nvidia-smi

# # dataset 압축 파일 풀기
# !unzip "datasets.zip"

# # ultralytics 설치
# !pip install ultralytics

from ultralytics import YOLO

model = YOLO('yolo11n.pt') # Nano 모델: 가장 가볍고 빠른 모델 (실시간성 최적화)

result = model.train(
    data='/content/refined_dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    patience=70,
    device=0,
    optimizer='SGD',
    
    # 📈 최적화: Stability & Generalization
    multi_scale=False,       # ZeroDivisionError 방지를 위해 비활성화 (Colab 환경 이슈)
    # label_smoothing=0.1,  # (Deprecated) 최신 버전에서 경고가 발생하여 제외
    
    # 증강 전략 최적화 (오프라인 증강과 밸런스 유지)
    hsv_h=0.015,        # 0.03 -> 0.015 (색조 변화 완화)
    hsv_s=0.5,          # 0.9 -> 0.5 (오프라인 채도와 중복 방지)
    hsv_v=0.4,          # 0.6 -> 0.4 (오프라인 밝기/감마와 중복 방지)
    degrees=10.0,       # 15 -> 10 (회전은 오프라인에서 주로 담당)
    translate=0.1,      # 0.2 -> 0.1
    scale=0.5,          # 0.7 -> 0.5
    shear=2.0,          # 5.0 -> 2.0
    perspective=0.0,    # 오프라인에서 담당
    flipud=0.5,
    fliplr=0.5,
    mosaic=1.0,
    mixup=0.1,          # 0.15 -> 0.1 (안정적인 데이터 품질 유지)
    overlap_mask=True,
    
    # 학습률 조정
    lr0=0.01,
    cos_lr=True,
)

print('============================학습 종료============================')

# 검증 실행 (최고 성능 가중치 사용)
print('============================검증 시작============================')
metrics = model.val() # 이전에 학습한 best.pt를 자동으로 사용하여 검증 수행
print(f"Validation mAP50-95: {metrics.box.map}")
print(f"Validation mAP50: {metrics.box.map50}")
print('============================검증 종료============================')