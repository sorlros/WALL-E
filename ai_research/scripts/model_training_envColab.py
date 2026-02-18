# # GPU 유무 확인
# !nvidia-smi

# # dataset 압축 파일 풀기
# !unzip "datasets.zip"

# # ultralytics 설치
# !pip install ultralytics

from ultralytics import YOLO

model = YOLO('yolo11s.pt') # Small 모델: Nano보다 약 3.6배 많은 파라미터로 균열 검출력 극대화 (GTX 1060 실시간 가능)

result = model.train(
    data='/content/refined_dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    patience=0,        # 끝까지 학습하도록 0으로 설정
    device=0,
    optimizer='SGD',    # AdamW보다 정교한 학습을 위해 SGD로 변경
    
    # 증강 전략 수정
    mosaic=1.0,        # 작은 균열 검출을 위해 필수
    mixup=0.1,         # 데이터가 적을 때 일반화 성능 향상
    overlap_mask=True,
    
    # 학습률 조정
    lr0=0.01,          # SGD 사용 시 전형적인 초기 학습률
    cos_lr=True,
)

print('============================학습 종료============================')

# 검증 실행 (최고 성능 가중치 사용)
print('============================검증 시작============================')
metrics = model.val() # 이전에 학습한 best.pt를 자동으로 사용하여 검증 수행
print(f"Validation mAP50-95: {metrics.box.map}")
print(f"Validation mAP50: {metrics.box.map50}")
print('============================검증 종료============================')