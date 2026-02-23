# # GPU 유무 확인
# !nvidia-smi

# # dataset 압축 파일 풀기
# !unzip "datasets.zip"

# # ultralytics 설치
# !pip install ultralytics

from ultralytics import YOLO

model = YOLO('yolo11s.pt') # Nano 모델: 가장 가볍고 빠른 모델 (실시간성 최적화)

result = model.train(
    data='/content/refined_dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device=0,
    optimizer='AdamW',      # 🛠 V4: AdamW 전환 (작은 모델 수렴에 유리)
    close_mosaic=20,        # 🛠 V4: 마지막 20에폭 동안 Mosaic 해제 (정교한 마무리)

    # 📈 최적화: Stability & Generalization
    multi_scale=False,

    # 증강 전략 최적화 (오프라인 증강과 밸런스 유지)
    # 증강 전략 최적화 (기본 증강으로 복구)
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    degrees=0.0,
    translate=0.1,
    scale=0.5,
    shear=0.0,
    perspective=0.0,
    flipud=0.0,
    fliplr=0.5,
    mosaic=1.0,
    mixup=0.0,
    overlap_mask=True,

    # 학습률 조정 (AdamW에 맞춰진 초기값)
    lr0=0.001,
    cos_lr=True,
)

print('============================학습 종료============================')

# 검증 실행 (최고 성능 가중치 사용)
print('============================검증 시작============================')
metrics = model.val() # 이전에 학습한 best.pt를 자동으로 사용하여 검증 수행
print(f"Validation mAP50-95: {metrics.box.map}")
print(f"Validation mAP50: {metrics.box.map50}")
print('============================검증 종료============================')