# # GPU 유무 확인
# !nvidia-smi

# # dataset 압축 파일 풀기
# !unzip "datasets.zip"

# # ultralytics 설치
# !pip install ultralytics

from ultralytics import YOLO

model = YOLO('yolo11s.pt') # Small 모델: Nano보다 정밀도가 높으며, 오탐지 줄이기에 유리함

result = model.train(
    data='/content/window_refined/data.yaml',
    epochs=30,
    imgsz=640,
    batch=16,
    device=0,
    optimizer='AdamW',      # 🛠 V4: AdamW 전환 (작은 모델 수렴에 유리)
    close_mosaic=20,        # 🛠 V4: 마지막 20에폭 동안 Mosaic 해제 (정교한 마무리)

    # 📈 최적화: Stability & Generalization
    multi_scale=False,

    # 증강 전략 최적화 (오프라인 증강과 밸런스 유지)
    hsv_h=0.015,
    hsv_s=0.5,
    hsv_v=0.4,
    degrees=5.0,        # 🛠 V4: 회전 범위를 좁혀 안정적 학습 (10 -> 5)
    translate=0.1,
    scale=0.5,
    shear=2.0,
    perspective=0.0,
    flipud=0.5,
    fliplr=0.5,
    mosaic=0.8,
    mixup=0.0,          # 🛠 V4: 순수 배경 데이터 학습에 집중하도록 비활성
    overlap_mask=True,

    # 학습률 조정 (AdamW에 맞춰진 초기값)
    lr0=0.001,
    cos_lr=True,
)

import shutil
import os

# 모델 이름 변경 저장 (best.pt -> best_w.pt)
best_model_path = 'runs/detect/train/weights/best_w.pt'
if os.path.exists(best_model_path):
    shutil.copy(best_model_path, 'best_w.pt')
    print(f"✅ 모델이 'best_w.pt'로 저장되었습니다.")

print('============================학습 종료============================')

# 검증 실행 (최고 성능 가중치 사용)
print('============================검증 시작============================')
metrics = model.val() # 이전에 학습한 best.pt를 자동으로 사용하여 검증 수행
print(f"Validation mAP50-95: {metrics.box.map}")
print(f"Validation mAP50: {metrics.box.map50}")
print('============================검증 종료============================')