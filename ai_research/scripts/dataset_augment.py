import albumentations as A
import cv2
import os
import numpy as np
import shutil
import random
import yaml
from tqdm import tqdm
from pathlib import Path

# --------------------------------------------------------------------------
# 🚁 드론 촬영 환경 고도화 증강 조건 (V14: Pure Crack Optimization)
# --------------------------------------------------------------------------
drone_transform = A.Compose([
    # 📐 1. 저해상도 원본 보호 (0.9~1.0: 이미 640인 이미지를 더 이상 쪼개지 않음)
    A.RandomResizedCrop(size=(640, 640), scale=(0.9, 1.0), p=0.4),
    
    # 📐 2. 뭉개진 엣지 강제 복구 (강도 상향)
    A.OneOf([
        A.Sharpen(alpha=(0.4, 0.6), p=1.0),
        A.CLAHE(clip_limit=5.0, p=1.0),
    ], p=0.7),
    
    # 📐 3. 부분 가림 시뮬레이션 (강도 조절)
    A.CoarseDropout(
        num_holes_range=(1, 3), 
        hole_height_range=(4, 12), 
        hole_width_range=(4, 12), 
        fill_value=0, 
        p=0.3
    ),

    # 🚫 4. 기하학적 왜곡 제거 (YOLO 내부 증강과 충돌 방지)
    # HorizontalFlip, Perspective -> YOLO 학습 시 적용

    # ☀️ 5. 조명 및 밝기 가변성
    A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.4),
], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels'], min_visibility=0.1, min_area=1))

def sanitize_and_save_labels(lbl_src, lbl_dst, output_name):
    """라벨 좌표가 1.0을 넘는 경우 [0, 1]로 클리핑하여 저장합니다."""
    if not os.path.exists(lbl_src): return False
    safe_bboxes = []
    with open(lbl_src, 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) < 5: continue
            cls = int(parts[0])
            raw_bbox = [float(x) for x in parts[1:5]]
            # 🛠 라벨 무결성 복구 로직 (V11: Boundary Clipping)
            x_c, y_c, w, h = raw_bbox
            x1, y1 = x_c - w/2, y_c - h/2
            x2, y2 = x_c + w/2, y_c + h/2
            
            x1, y1 = max(0.0, min(1.0, x1)), max(0.0, min(1.0, y1))
            x2, y2 = max(0.0, min(1.0, x2)), max(0.0, min(1.0, y2))
            
            new_w, new_h = x2 - x1, y2 - y1
            new_x, new_y = x1 + new_w/2, y1 + new_h/2
            
            if new_w > 0.001 and new_h > 0.001:
                safe_bboxes.append([0, new_x, new_y, new_w, new_h]) # Pure Crack (Class 0)
    
    if not safe_bboxes: return False
    with open(os.path.join(lbl_dst, f"{output_name}.txt"), 'w') as f:
        for b in safe_bboxes:
            f.write(f"{b[0]} {' '.join([f'{x:.6f}' for x in b[1:]])}\n")
    return True

def augment_yolo(img_path, lbl_path, img_out, lbl_out, transform, suffix=""):
    """YOLO 데이터를 증강하여 저장합니다."""
    img_array = np.fromfile(img_path, np.uint8)
    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if image is None: return False
    
    bboxes, class_labels = [], []
    if os.path.exists(lbl_path):
        with open(lbl_path, 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) < 5: continue
                
                raw_bbox = [float(x) for x in parts[1:5]]
                x_c, y_c, w, h = raw_bbox
                x1, y1 = x_c - w/2, y_c - h/2
                x2, y2 = x_c + w/2, y_c + h/2
                x1, y1 = max(0.0, min(1.0, x1)), max(0.0, min(1.0, y1))
                x2, y2 = max(0.0, min(1.0, x2)), max(0.0, min(1.0, y2))
                new_w, new_h = x2 - x1, y2 - y1
                new_x, new_y = x1 + new_w/2, y1 + new_h/2

                if new_w > 0.001 and new_h > 0.001:
                    bboxes.append([new_x, new_y, new_w, new_h])
                    class_labels.append(0) # Pure Crack (Class 0)

    if not bboxes: return False
    output_name = Path(img_path).stem + (f"_{suffix}" if suffix else "")
    
    try:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        augmented = transform(image=image_rgb, bboxes=bboxes, class_labels=class_labels)
        if not augmented['bboxes']: return False
        
        image_aug = cv2.cvtColor(augmented['image'], cv2.COLOR_RGB2BGR)
        _, img_encoded = cv2.imencode(".jpg", image_aug)
        img_encoded.tofile(os.path.join(img_out, f"{output_name}.jpg"))
        with open(os.path.join(lbl_out, f"{output_name}.txt"), 'w') as f:
            for cls, bbox in zip(augmented['class_labels'], augmented['bboxes']):
                f.write(f"{cls} {' '.join([f'{x:.6f}' for x in bbox])}\n")
        return True
    except Exception as e:
        # print(f"Error augmenting {img_path}: {e}")
        return False

def process_dataset(input_root, output_root, val_ratio=0.2):
    input_root, output_root = Path(input_root), Path(output_root)
    train_src = input_root / "train"
    if not train_src.exists():
        print(f"Error: 'train' folder not found at {input_root}")
        return

    img_files = list((train_src / "images").glob("*.jpg"))
    random.seed(42)
    random.shuffle(img_files)
    
    split_idx = int(len(img_files) * (1 - val_ratio))
    split_data = {'train': img_files[:split_idx], 'val': img_files[split_idx:]}

    print(f"V11 Pipeline: Train({len(split_data['train'])}), Val({len(split_data['val'])})")

    for split, files in split_data.items():
        img_dst, lbl_dst = output_root / split / 'images', output_root / split / 'labels'
        os.makedirs(img_dst, exist_ok=True); os.makedirs(lbl_dst, exist_ok=True)
        
        print(f"Processing {split} split (Auto-Filtering Backgrounds in Val)...")
        for img_path in tqdm(files):
            lbl_path = train_src / "labels" / f"{img_path.stem}.txt"
            
            # 🔍 V11 핵심: 검증 세트에서 배경 이미지 제외 (mAP 희석 방지)
            if split == 'val':
                if not sanitize_and_save_labels(str(lbl_path), str(lbl_dst), img_path.stem):
                    continue # 라벨이 없는 경우 이미지도 복사하지 않음
                shutil.copy(str(img_path), str(img_dst / img_path.name))
            else:
                # 훈련 세트는 배경 이미지 포함 (오검출 방지 학습용)
                shutil.copy(str(img_path), str(img_dst / img_path.name))
                sanitize_and_save_labels(str(lbl_path), str(lbl_dst), img_path.stem)
                
                # 훈련 세트 증강 (3배)
                for i in range(1, 4):
                    augment_yolo(str(img_path), str(lbl_path), str(img_dst), str(lbl_dst), 
                                 drone_transform, suffix=f"v7_{i}")

    # data.yaml 생성
    yaml_data = {
        'path': '/content/refined_dataset', # 코랩 환견에서의 경로 ; 변경 금지
        'train': 'train/images', 
        'val': 'val/images', 
        'names': {0: 'crack'}
        }
    with open(output_root / 'data.yaml', 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False)
    print(f"\nV14.1 Pipeline Completed! Saved to: {output_root}")

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    INPUT_DIR = BASE_DIR / "datasets" / "concrete_crack"
    OUTPUT_DIR = BASE_DIR / "datasets" / "refined_dataset"
    if INPUT_DIR.exists():
        process_dataset(INPUT_DIR, OUTPUT_DIR)
    else:
        print(f"Error: Dataset not found at {INPUT_DIR}")
