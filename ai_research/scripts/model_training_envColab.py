# # GPU 유무 확인
# !nvidia-smi

# # dataset 압축 파일 풀기
# !unzip "datasets.zip"

# # ultralytics 설치
# !pip install ultralytics

from ultralytics import YOLO

model = YOLO("yolo11n.pt")

result = model.train(
    data='C:/Users/User/Desktop/Intel_AI_education/CV_Project/WallE/ai_research/datasets/final_split_dataset/data.yaml',
    epochs=50,
    imgsz=640,
    batch=8,
    name='augmentation_result',
    device='CPU',

    # ========= [데이터 증강 끄기 설정] ========= #
    hsv_h=0.0,                  # 색조 변경 끄기
    hsv_s=0.0,                  # 채도 변경 끄기
    hsv_v=0.0,                  # 명도 변경 끄기
    degrees=0.0,                # 회전 끄기
    translate=0.0,              # 이동 끄기
    scale=0.0,                  # 스케일 변경 끄기
    shear=0.0,                  # 전단 변환 끄기
    perspective=0.0,            # 원근 변환 끄기
    flipud=0.0,                 # 상하 반전 끄기
    fliplr=0.0,                 # 좌우 반전 끄기
    mosaic=0.0,                 # 모자이크(4장 합치기) 끄기 (★중요)
    mixup=0.0,                  # 믹스업 끄기
    copy_paste=0.0,             # 복사 붙여넣기 끄기
    auto_augment=None,          # 자동 증강(RandAugment 등) 끄기
    erasing=0.0,                # 랜덤 지우기 끄기
    # blur=0.0,                   # 블러 끄기
    # median=0.0,                 # 미디언 필터 끄기
    # clahe=0.0,                  # CLAHE 끄기
    crop_fraction=1.0,          # 이미지 크롭 비율 (1.0 = 크롭 없음)
    bgr=0.0,                    # 채널 순서 섞기 끄기
    rect=False,                 # 사각형 학습(Rectangular training) 끄기
)

print('============================학습 종료============================')

# 검증 실행 (최고 성능 가중치 사용)
print('============================검증 시작============================')
metrics = model.val() # 이전에 학습한 best.pt를 자동으로 사용하여 검증 수행
print(f"Validation mAP50-95: {metrics.box.map}")
print(f"Validation mAP50: {metrics.box.map50}")
print('============================검증 종료============================')