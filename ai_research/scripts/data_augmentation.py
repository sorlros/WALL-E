import albumentations as A
import cv2
import os
import json
import numpy as np
import shutil
from tqdm import tqdm

def convert_coco_to_yolo(coco_json_path, img_dir, output_dir):
    """COCO format annotations를 YOLO format(.txt)으로 변환하고 이미지를 복사합니다."""
    with open(coco_json_path, 'r') as f:
        data = json.load(f)

    # Output directory setup
    img_output = os.path.join(output_dir, 'images')
    lbl_output = os.path.join(output_dir, 'labels')
    os.makedirs(img_output, exist_ok=True)
    os.makedirs(lbl_output, exist_ok=True)

    # Category mapping (coco starts from 0 or 1, yolo starts from 0)
    cat_id_map = {cat['id']: i for i, cat in enumerate(data['categories'])}
    
    images = {img['id']: img for img in data['images']}
    annotations = data['annotations']

    for img_id, img_info in tqdm(images.items(), desc="Processing Original Images"):
        file_name = img_info['file_name']
        width = img_info['width']
        height = img_info['height']
        
        # Copy original image
        src_path = os.path.join(img_dir, file_name)
        dst_path = os.path.join(img_output, file_name)
        if os.path.exists(src_path):
            shutil.copy(src_path, dst_path)
        else:
            print(f"Warning: {src_path} not found.")
            continue

        # Create YOLO label file
        label_file = os.path.splitext(file_name)[0] + '.txt'
        label_path = os.path.join(lbl_output, label_file)
        
        with open(label_path, 'w') as f:
            for ann in annotations:
                if ann['image_id'] == img_id:
                    cat_id = cat_id_map[ann['category_id']]
                    bbox = ann['bbox'] # [x, y, w, h]
                    
                    # Normalize to [0, 1]
                    x_center = (bbox[0] + bbox[2] / 2) / width
                    y_center = (bbox[1] + bbox[3] / 2) / height
                    w = bbox[2] / width
                    h = bbox[3] / height
                    
                    f.write(f"{cat_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")

    return img_output, lbl_output

# 1. 현장 맞춤형 (Real-world): 카카오톡 영상/모바일 조건
real_world_transform = A.Compose([
    A.ImageCompression(quality_lower=20, quality_upper=50, p=0.5), # 카톡 화질 저하
    A.MotionBlur(blur_limit=7, p=0.4), # 흔들림
    A.GaussNoise(var_limit=(10.0, 50.0), p=0.3), # 센서 노이즈
    A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.5), # 조명 변화
    A.SafeRotate(limit=15, p=0.3), # 미세 회전
], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))

# 2. 성능 최적화 추천 (Recommended): 균열 탐지 디테일 위주
recommended_transform = A.Compose([
    A.Sharpen(alpha=(0.2, 0.5), lightness=(0.5, 1.0), p=0.5), # 균열 선명도 강화
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.5),
    A.RandomResizedCrop(height=640, width=640, scale=(0.8, 1.0), p=0.4), # 스케일 변화
    A.CLAHE(clip_limit=4.0, p=0.4), # 로컬 대비 강화
], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))

def apply_augmentation(img_dir, lbl_dir, output_dir, transform, suffix):
    img_output = os.path.join(output_dir, 'images')
    lbl_output = os.path.join(output_dir, 'labels')
    os.makedirs(img_output, exist_ok=True)
    os.makedirs(lbl_output, exist_ok=True)

    image_files = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    for img_file in tqdm(image_files, desc=f"Applying {suffix} Augmentation"):
        img_path = os.path.join(img_dir, img_file)
        lbl_path = os.path.join(lbl_dir, os.path.splitext(img_file)[0] + '.txt')
        
        if not os.path.exists(lbl_path):
            continue

        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        bboxes = []
        class_labels = []
        with open(lbl_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                class_labels.append(int(parts[0]))
                bboxes.append([float(x) for x in parts[1:]])

        try:
            augmented = transform(image=image, bboxes=bboxes, class_labels=class_labels)
            aug_image = augmented['image']
            aug_bboxes = augmented['bboxes']
            
            # Save augmented image
            new_img_name = f"{os.path.splitext(img_file)[0]}_{suffix}.jpg"
            cv2.imwrite(os.path.join(img_output, new_img_name), cv2.cvtColor(aug_image, cv2.COLOR_RGB2BGR))
            
            # Save augmented labels
            new_lbl_name = f"{os.path.splitext(img_file)[0]}_{suffix}.txt"
            with open(os.path.join(lbl_output, new_lbl_name), 'w') as f:
                for cls, bbox in zip(class_labels, aug_bboxes):
                    f.write(f"{cls} {' '.join([f'{x:.6f}' for x in bbox])}\n")
        except Exception as e:
            print(f"Error augmenting {img_file}: {e}")

if __name__ == "__main__":
    # Settings
    # 스크립트 파일(ai_research/scripts/data_augmentation.py)의 위치를 기준으로 경로 설정
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    AI_RESEARCH_DIR = os.path.dirname(SCRIPT_DIR)
    
    # 입력 데이터 경로: ai_research/merged_dataset/merged_dataset
    INPUT_DIR = os.path.join(AI_RESEARCH_DIR, "merged_dataset", "merged_dataset")
    COCO_JSON = os.path.join(INPUT_DIR, "_annotations.coco.json")
    ORIG_IMG_DIR = INPUT_DIR
    
    # 출력 데이터 경로: ai_research/crack_yolo (ai_research 폴더 내부로 제한)
    YOLO_DIR = os.path.join(AI_RESEARCH_DIR, "crack_yolo") 
    
    print(f"Step 1: COCO to YOLO Conversion...")
    print(f"Input JSON: {COCO_JSON}")
    print(f"Output DIR: {YOLO_DIR}")
    
    if not os.path.exists(COCO_JSON):
        print(f"Error: {COCO_JSON} 파일을 찾을 수 없습니다.")
    else:
        img_orig, lbl_orig = convert_coco_to_yolo(COCO_JSON, ORIG_IMG_DIR, YOLO_DIR)
        
        print("/nStep 2: Applying Real-world Augmentation...")
        apply_augmentation(img_orig, lbl_orig, YOLO_DIR, real_world_transform, "real")
        
        print("/nStep 3: Applying Recommended Augmentation...")
        apply_augmentation(img_orig, lbl_orig, YOLO_DIR, recommended_transform, "rec")

        print(f"/nAll steps completed! Dataset is ready in: {YOLO_DIR}")
        print(f"Total images: {len(os.listdir(os.path.join(YOLO_DIR, 'images')))}")
