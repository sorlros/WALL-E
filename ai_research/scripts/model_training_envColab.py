# # GPU 유무 확인
# !nvidia-smi

# # dataset 압축 파일 풀기
# !unzip "datasets.zip"

# # ultralytics 설치
# !pip install ultralytics

from ultralytics import YOLO

model = YOLO('yolo11s.pt') # mAP 0.5+를 위한 시력 상향

result = model.train(
    data='/content/refined_dataset/data.yaml',
    epochs=200,        # SGD 수렴을 위해 넉넉하게 설정
    imgsz=640,
    batch=16,          # Small 모델 체급 고려하여 조정
    patience=100,      # 조기 종료 방지

    # ========= [V12 학습 최적화: SGD Stability] ========= #
    optimizer='SGD',
    lr0=0.01,
    momentum=0.937,
    weight_decay=0.0005,
    cos_lr=True,

    # ========= [V12 증강 전략: "Back to Basics"] ========= #
    # 1024px 오프라인 증강 데이터의 품질을 보존하기 위해 실시간 노이즈 최소화
    mosaic=0.0,        
    mixup=0.0,         
    fliplr=0.5,        
    flipud=0.0,
    degrees=0.0,
    translate=0.0,     # Offline Crop이 이미 수행
    scale=0.0,         # Offline Crop이 이미 수행
    shear=0.0,
    perspective=0.0,
    
    # 색상 변환 (미세 조정)
    hsv_h=0.01,
    hsv_s=0.5,
    hsv_v=0.3,
)

print('============================학습 종료============================')

# 검증 실행 (최고 성능 가중치 사용)
print('============================검증 시작============================')
metrics = model.val() # 이전에 학습한 best.pt를 자동으로 사용하여 검증 수행
print(f"Validation mAP50-95: {metrics.box.map}")
print(f"Validation mAP50: {metrics.box.map50}")
print('============================검증 종료============================')

from google.colab import runtime
print('학습이 완료되었습니다. 런타임을 종료합니다.')
runtime.unassign()