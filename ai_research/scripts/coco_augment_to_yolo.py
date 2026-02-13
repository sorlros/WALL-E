import albumentations as A
import cv2
import os
import json
import numpy as np
import shutil
from tqdm import tqdm
from pathlib import Path

# --------------------------------------------------------------------------
# 🚁 드론 촬영 환경 (3m 거리, 정면 고정, 수직 이동) 최적화 증강 조건
# --------------------------------------------------------------------------
drone_transform = A.Compose([
    # 📐 기하학적 변화 (Geometry)
    A.HorizontalFlip(p=0.5), # 좌우 반전: 균열 방향에 상관없이 학습
    A.SafeRotate(limit=15, p=0.4), # 회전: 드론이 비행 중 바람 등으로 약간 기울어진 상태 (±15도)

    # 💨 촬영 환경 및 수직 이동 강조 (Vertical Focus & Stable Motion)
    # 왜곡(Distortion)은 제외하고, 수직 이동(Shift)에 중점을 둠
    A.ShiftScaleRotate(
        shift_limit_x=0.02, # 수평 이동 최소화
        shift_limit_y=0.15, # 수직 이동 강조 (고도 변화 모사)
        scale_limit=0.05,    # 3m 거리 고정이므로 스케일 변화는 최소화 (±5%)
        rotate_limit=0,      # 회전은 위 SafeRotate에서 처리하므로 0
        p=0.5
    ),

    # ☀️ 조명 및 날씨 변화 (Lighting & Weather)
    A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.5), # 햇빛, 구름, 그림자 시뮬레이션
    A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20, p=0.3), # 시간대별 색감 차이
    A.ISONoise(color_shift=(0.01, 0.05), intensity=(0.1, 0.5), p=0.3), # 저조도 센서 노이즈
    
    # CLAHE(대비 강조)와 Sharpening(선명화) + 흑백 전환================================
    A.ToGray(p=0.2), # 흑백 전환: 색상 정보가 없는 환경에서도 강건하게 인식하도록 학습

    # ✨ 이미지 품질 및 선명도 (Quality & Sharpness)
    A.CLAHE(clip_limit=4.0, p=0.4), # 대비 강조: 미세한 균열과 배경의 차이를 극대화
    A.Sharpen(alpha=(0.2, 0.5), lightness=(0.5, 1.0), p=0.4), # 선명화: 뭉개진 균열 선을 뚜렷하게 보정
    #==============================================================================

    # 💨 환경 변화 및 카메라 효과 (Camera Effects)
    A.MotionBlur(blur_limit=7, p=0.3), # 드론 이동 시 흔들림 (수직 위주)
    A.GaussianBlur(blur_limit=(3, 7), p=0.3), # 포커스가 살짝 나간 상태 모사
], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))

def coco_to_yolo_normalized(coco_json_path, img_dir, output_dir):
    """
    COCO JSON을 읽어 YOLO 형식으로 변환합니다.
    모든 라벨은 'defect' (ID 0)으로 강제 통일됩니다.
    """
    print(f"Loading COCO JSON from: {coco_json_path}")
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)

    img_output = os.path.join(output_dir, 'images')
    lbl_output = os.path.join(output_dir, 'labels')
    os.makedirs(img_output, exist_ok=True)
    os.makedirs(lbl_output, exist_ok=True)

    images = {img['id']: img for img in coco_data['images']}
    
    # annotations를 이미지 ID별로 그룹화
    img_id_to_ann = {}
    for ann in coco_data['annotations']:
        img_id = ann['image_id']
        if img_id not in img_id_to_ann:
            img_id_to_ann[img_id] = []
        img_id_to_ann[img_id].append(ann)

    print(f"Processing {len(images)} images (Converting to YOLO format)...")
    
    for img_id, img_info in tqdm(images.items()):
        file_name = img_info['file_name']
        img_w = float(img_info['width'])
        img_h = float(img_info['height'])
        
        # 이미지 파일 로드 및 원본 저장
        src_path = os.path.join(img_dir, file_name)
        dst_path = os.path.join(img_output, file_name)
        
        if os.path.exists(src_path):
            shutil.copy(src_path, dst_path)
        else:
            continue

        # YOLO 라벨 파일 생성
        txt_name = Path(file_name).stem + ".txt"
        txt_path = os.path.join(lbl_output, txt_name)
        
        anns = img_id_to_ann.get(img_id, [])
        
        with open(txt_path, 'w') as f:
            for ann in anns:
                # 모든 라벨을 0 (defect)으로 고정
                yolo_cls = 0
                
                # Bbox: [x_min, y_min, width, height]
                bbox = [float(x) for x in ann['bbox']]
                x_min, y_min, w, h = bbox
                
                # Center-normalized coordinates
                x_center = (x_min + w / 2) / img_w
                y_center = (y_min + h / 2) / img_h
                w_n = w / img_w
                h_n = h / img_h
                
                # Clipping
                x_center = max(0, min(1.0, x_center))
                y_center = max(0, min(1.0, y_center))
                w_n = max(0, min(1.0, w_n))
                h_n = max(0, min(1.0, h_n))
                
                f.write(f"{yolo_cls} {x_center:.6f} {y_center:.6f} {w_n:.6f} {h_n:.6f}\n")

    return img_output, lbl_output

def apply_augmentation(img_dir, lbl_dir, output_dir, transform, suffix="aug"):
    """
    YOLO 형식의 데이터셋에 증강을 적용합니다.
    """
    img_output = os.path.join(output_dir, 'images')
    lbl_output = os.path.join(output_dir, 'labels')
    os.makedirs(img_output, exist_ok=True)
    os.makedirs(lbl_output, exist_ok=True)

    image_files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    
    print(f"Applying '{suffix}' Augmentation to {len(image_files)} images...")
    
    for img_file in tqdm(image_files):
        img_path = os.path.join(img_dir, img_file)
        lbl_path = os.path.join(lbl_dir, Path(img_file).stem + '.txt')
        
        if not os.path.exists(lbl_path):
            continue

        # 이미지 로드 (경로 한글 지원을 위해 np.fromfile 사용)
        try:
            img_array = np.fromfile(img_path, np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if image is None: continue
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        except:
            continue
        
        bboxes = []
        class_labels = []
        with open(lbl_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5: continue
                class_labels.append(int(parts[0]))
                bboxes.append([float(x) for x in parts[1:]])

        if not bboxes: continue

        try:
            augmented = transform(image=image, bboxes=bboxes, class_labels=class_labels)
            aug_image = augmented['image']
            aug_bboxes = augmented['bboxes']
            
            # 증강 이미지 저장
            new_img_name = f"{Path(img_file).stem}_{suffix}.jpg"
            save_path = os.path.join(img_output, new_img_name)
            
            res, img_encoded = cv2.imencode(".jpg", cv2.cvtColor(aug_image, cv2.COLOR_RGB2BGR))
            if res:
                img_encoded.tofile(save_path)
            
            # 증강 라벨 저장
            new_lbl_name = f"{Path(img_file).stem}_{suffix}.txt"
            with open(os.path.join(lbl_output, new_lbl_name), 'w') as f:
                for cls, bbox in zip(class_labels, aug_bboxes):
                    f.write(f"{cls} {' '.join([f'{x:.6f}' for x in bbox])}\n")
        except:
            continue

if __name__ == "__main__":
    # 경로 설정
    BASE_DIR = Path(__file__).resolve().parent.parent
    INPUT_DIR = BASE_DIR / "datasets" / "defect_review" / "train" # 예시 경로
    COCO_JSON = INPUT_DIR / "_annotations.coco.json"
    
    # 출력 경로
    OUTPUT_DIR = BASE_DIR / "datasets" / "augmented_yolo_dataset"
    
    if COCO_JSON.exists():
        # 1단계: COCO -> YOLO 변환 (라벨 defect로 통일)
        print("Step 1: Converting COCO to YOLO with normalized labels (class: defect)...")
        img_orig, lbl_orig = coco_to_yolo_normalized(str(COCO_JSON), str(INPUT_DIR), str(OUTPUT_DIR))
        
        # 2단계: 데이터 증강 적용
        print("\nStep 2: Applying Drone-Optimized Augmentation...")
        apply_augmentation(img_orig, lbl_orig, str(OUTPUT_DIR), drone_transform, suffix="drone")
        
        print(f"\nCompleted! Dataset saved in: {OUTPUT_DIR}")
    else:
        print(f"Error: COCO JSON not found at {COCO_JSON}")
        print("Please update the INPUT_DIR in the script to match your dataset path.")
