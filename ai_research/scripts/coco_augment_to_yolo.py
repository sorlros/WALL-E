import albumentations as A
import cv2
import os
import json
import numpy as np
import shutil
import random
import yaml
from tqdm import tqdm
from pathlib import Path

# --------------------------------------------------------------------------
# 🚁 드론 촬영 환경 고도화 증강 조건 (Enhanced Drone Augmentation)
# --------------------------------------------------------------------------
drone_transform = A.Compose([
    # 📐 기하학적 변화 (Geometry)
    A.HorizontalFlip(p=0.5), 
    A.VerticalFlip(p=0.2),   # 수직 반전 추가
    A.SafeRotate(limit=20, p=0.4), # 회전 범위 확대

    # 렌즈 왜곡 (Lens Distortion) - 드론 카메라 특성 반영
    A.OneOf([
        A.OpticalDistortion(distort_limit=0.1, shift_limit=0.1, p=1.0),
        A.GridDistortion(num_steps=5, distort_limit=0.1, p=1.0),
    ], p=0.3),

    # 💨 촬영 환경 및 수직 이동 강조 (Vertical Focus & Stable Motion)
    A.ShiftScaleRotate(
        shift_limit_x=0.05, 
        shift_limit_y=0.2,   # 수직 이동 범위 확대 (고도 변화)
        scale_limit=0.1,     # 거리 변화 모사 (±10%)
        rotate_limit=10,
        p=0.5
    ),

    # ☀️ 조명 및 그림자 (Lighting & Shadows)
    A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.5),
    A.RandomShadow(shadow_roi=(0, 0.5, 1, 1), num_shadows_lower=1, num_shadows_upper=3, p=0.3), # 그림자 추가
    A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20, p=0.3),
    
    # 🌫 노이즈 및 가림 (Noise & Occlusion)
    A.ISONoise(color_shift=(0.01, 0.05), intensity=(0.1, 0.5), p=0.3),
    A.CoarseDropout(max_holes=8, max_height=32, max_width=32, min_holes=1, p=0.3), # 구조물 등에 의한 부분 가림 모사
    
    # 대비 강조 및 선명화
    A.CLAHE(clip_limit=4.0, p=0.4), 
    A.Sharpen(alpha=(0.2, 0.5), lightness=(0.5, 1.0), p=0.4),

    # 💨 카메라 흔들림 (Motion)
    A.OneOf([
        A.MotionBlur(blur_limit=7, p=1.0),
        A.GaussianBlur(blur_limit=(3, 7), p=1.0),
    ], p=0.4),
], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))

def process_and_save(img_info, anns, img_dir, img_out, lbl_out, transform=None, suffix=""):
    """이미지와 어노테이션을 처리하여 YOLO 형식으로 저장합니다. (증강 가능)"""
    file_name = img_info['file_name']
    img_w, img_h = float(img_info['width']), float(img_info['height'])
    
    # 1. 이미지 로드
    src_path = os.path.join(img_dir, file_name)
    if not os.path.exists(src_path): return False
    
    try:
        img_array = np.fromfile(src_path, np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if image is None: return False
    except: return False

    # 2. 라벨 준비 (ID 0: defect로 고정)
    bboxes = []
    class_labels = []
    for ann in anns:
        x_min, y_min, w, h = [float(x) for x in ann['bbox']]
        # Valid bbox check (Albumentations requires positive area)
        if w <= 0 or h <= 0: continue
        
        # Center-normalized YOLO format
        x_c = (x_min + w / 2) / img_w
        y_c = (y_min + h / 2) / img_h
        wn = w / img_w
        hn = h / img_h
        bboxes.append([x_c, y_c, wn, hn])
        class_labels.append(0) # All defect

    if not bboxes: return False

    # 3. 증강 적용 (있는 경우)
    output_name = Path(file_name).stem
    if suffix: output_name += f"_{suffix}"
    
    if transform:
        try:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            augmented = transform(image=image_rgb, bboxes=bboxes, class_labels=class_labels)
            
            # 증강 후 바운딩 박스가 사라지는 경우(필터링 등) 대응
            if not augmented['bboxes']: return False
            
            image = cv2.cvtColor(augmented['image'], cv2.COLOR_RGB2BGR)
            bboxes = augmented['bboxes']
            class_labels = augmented['class_labels']
        except Exception as e: 
            return False

    # 4. 저장
    img_save_path = os.path.join(img_out, f"{output_name}.jpg")
    lbl_save_path = os.path.join(lbl_out, f"{output_name}.txt")
    
    # 이미지 저장 (한글 경로 대응)
    res, img_encoded = cv2.imencode(".jpg", image)
    if res: img_encoded.tofile(img_save_path)
    
    # 라벨 저장
    with open(lbl_save_path, 'w') as f:
        for cls, bbox in zip(class_labels, bboxes):
            f.write(f"{cls} {' '.join([f'{x:.6f}' for x in bbox])}\n")
            
    return True

def run_pipeline(coco_json_path, img_dir, output_root, train_ratio=0.8):
    print(f"Loading COCO JSON: {coco_json_path}")
    with open(coco_json_path, 'r') as f:
        data = json.load(f)

    images = data['images']
    random.seed(42)
    random.shuffle(images)

    split_idx = int(len(images) * train_ratio)
    train_images = images[:split_idx]
    val_images = images[split_idx:]

    img_id_to_ann = {}
    for ann in data['annotations']:
        img_id = ann['image_id']
        if img_id not in img_id_to_ann: img_id_to_ann[img_id] = []
        img_id_to_ann[img_id].append(ann)

    # 폴더 구조 생성
    for split in ['train', 'val']:
        os.makedirs(os.path.join(output_root, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(output_root, split, 'labels'), exist_ok=True)

    # 훈련 세트 처리 (원본 + 증강 3종)
    print(f"Processing Train Set ({len(train_images)} original images)...")
    for img_info in tqdm(train_images):
        anns = img_id_to_ann.get(img_info['id'], [])
        # 1. 원본 저장
        process_and_save(img_info, anns, img_dir, 
                         os.path.join(output_root, 'train', 'images'), 
                         os.path.join(output_root, 'train', 'labels'))
        # 2. 증강본 3장 생성 (Diversity 확대)
        for i in range(1, 4):
            process_and_save(img_info, anns, img_dir, 
                             os.path.join(output_root, 'train', 'images'), 
                             os.path.join(output_root, 'train', 'labels'),
                             transform=drone_transform, suffix=f"drone{i}")

    # 검증 세트 처리 (원본 + 증강 1종)
    print(f"Processing Validation Set ({len(val_images)} original images)...")
    for img_info in tqdm(val_images):
        anns = img_id_to_ann.get(img_info['id'], [])
        # 원본 저장
        process_and_save(img_info, anns, img_dir, 
                         os.path.join(output_root, 'val', 'images'), 
                         os.path.join(output_root, 'val', 'labels'))
        # 증강본 1장 (드론 환경 테스트용)
        process_and_save(img_info, anns, img_dir, 
                         os.path.join(output_root, 'val', 'images'), 
                         os.path.join(output_root, 'val', 'labels'),
                         transform=drone_transform, suffix="drone")

    # data.yaml 생성
    yaml_data = {
        'path': os.path.abspath(output_root).replace('\\', '/'),
        'train': 'train/images',
        'val': 'val/images',
        'names': {0: 'defect'}
    }
    with open(os.path.join(output_root, 'data.yaml'), 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False)

    print(f"\nPipeline Completed! Data saved in: {output_root}")

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    # 입력 정보 설정
    INPUT_DIR = BASE_DIR / "datasets" / "defect_review" / "train" # COCO 데이터 위치
    COCO_JSON = INPUT_DIR / "_annotations.coco.json"
    
    # 출력 정보 설정
    OUTPUT_ROOT = BASE_DIR / "datasets" / "refined_dataset"
    
    if COCO_JSON.exists():
        run_pipeline(str(COCO_JSON), str(INPUT_DIR), str(OUTPUT_ROOT))
    else:
        print(f"Error: COCO JSON not found at {COCO_JSON}")
