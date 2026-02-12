# # GPU 유무 확인
# !nvidia-smi

# # dataset 압축 파일 풀기
# !unzip "datasets.zip"

# # ultralytics 설치
# !pip install ultralytics

model = YOLO("yolo11n.pt")

result = model.train(
    data='/content/datasets/data.yaml',
    epochs=10,
    imgsz=640,
    batch=30,
    name='augmentation_result',
    device='0',

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
    erasing=0.0,                # 랜덤 지우기 끄기
)

print('============================학습 종료============================')