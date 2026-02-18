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
# 🚁 드론 비행 시나리오 최적화 증강 조건 (V15: Vertical & Stable Focus)
# --------------------------------------------------------------------------
drone_transform = A.Compose([
    # 📐 1. 기하학적 변화 (Geometry & Stable Shooting)
    A.HorizontalFlip(p=0.5), # 좌우 반전 (데이터 2배 효과)
    A.ShiftScaleRotate(
        shift_limit_x=0.03,    # 수평 이동 최소화 (정면 고정)
        shift_limit_y=0.12,    # 수직 이동 강조 (수직 점검 비행)
        scale_limit=0.1,      # 3m 거리 유지 오차 시뮬레이션
        rotate_limit=15,      # 드론 기울어짐 (SafeRotate)
        border_mode=cv2.BORDER_CONSTANT,
        p=0.7
    ),
    
    # 💨 2. 촬영 환경 및 수직 모션 (Camera Effects / Vertical Focus)
    A.OneOf([
        A.MotionBlur(blur_limit=(3, 7), p=1.0), # 비행 중 흔들림
        A.GaussianBlur(blur_limit=(3, 7), p=1.0), # 초점 흐림
    ], p=0.4),

    # ☀️ 3. 조명 및 날씨 변화 (Lighting & Weather)
    A.RandomBrightnessContrast(
        brightness_limit=0.3, 
        contrast_limit=0.3, 
        p=0.5
    ), # 일조량 변화
    A.HueSaturationValue(
        hue_shift_limit=15, 
        sat_shift_limit=25, 
        val_shift_limit=15, 
        p=0.3
    ), # 센서 및 시간대별 색감
    A.ISONoise(
        color_shift=(0.01, 0.03), 
        intensity=(0.1, 0.4), 
        p=0.3
    ), # 저조도 센서 노이즈

    # 🩹 4. 미세 균열 가시성 강화 (Fixed Strategy)
    A.OneOf([
        A.Sharpen(alpha=(0.2, 0.4), p=1.0),
        A.CLAHE(clip_limit=3.0, p=1.0),
    ], p=0.4),
], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels'], min_visibility=0.1, min_area=1))

def sanitize_and_save_labels(lbl_src, lbl_dst, output_name):
    """라벨 좌표가 1.0을 넘는 경우 [0, 1]로 클리핑하여 저장합니다.
    라벨이 없거나 유효한 박스가 없는 경우 빈 파일을 생성하여 배경 이미지임을 표시합니다.
    """
    safe_bboxes = []
    if os.path.exists(lbl_src):
        with open(lbl_src, 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) < 5: continue
                # cls = int(parts[0]) # 현재는 단일 클래스(0: crack)만 처리
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
    
    # 배경 이미지(Null)이더라도 빈 라벨 파일을 생성하여 YOLO 학습 시 명시적인 배경으로 활용
    with open(os.path.join(lbl_dst, f"{output_name}.txt"), 'w') as f:
        for b in safe_bboxes:
            f.write(f"{b[0]} {' '.join([f'{x:.6f}' for x in b[1:]])}\n")
    return True # 이제 항상 True를 반환 (빈 파일이라도 생성하므로)

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

    # bboxes가 없어도 이미지 변환(조명, 노이즈 등)을 위해 진행
    output_name = Path(img_path).stem + (f"_{suffix}" if suffix else "")
    
    try:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        augmented = transform(image=image_rgb, bboxes=bboxes, class_labels=class_labels)
        # bboxes가 없는 경우에도 image 결과는 반환됨
        
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
    
    # v5i/v6i 데이터셋 구조에서 모든 이미지와 라벨 수집 기초 작업
    defect_imgs = []
    bg_imgs = []
    
    for split_dir in ['train', 'valid', 'test']:
        img_dir = input_root / split_dir / "images"
        if img_dir.exists():
            for img_path in img_dir.glob("*.jpg"):
                lbl_path = img_path.parent.parent / "labels" / f"{img_path.stem}.txt"
                
                # 라벨 파일 존재 여부 및 내용 확인하여 결함/배경 분류
                is_bg = True
                if lbl_path.exists():
                    with open(lbl_path, 'r') as f:
                        if f.read().strip(): # 내용이 있으면 결함
                            is_bg = False
                
                if is_bg:
                    bg_imgs.append(img_path)
                else:
                    defect_imgs.append(img_path)
    
    if not defect_imgs:
        print(f"Error: No defect images found in {input_root}")
        return

    # 🛠 V17: Background Capping (결함 대비 10%로 제한)
    random.seed(42)
    max_bg_count = int(len(defect_imgs) * 0.1)
    if len(bg_imgs) > max_bg_count:
        print(f"V17 Pipeline: Reducing backgrounds from {len(bg_imgs)} to {max_bg_count} (10% of defects)")
        bg_imgs = random.sample(bg_imgs, max_bg_count)
    
    all_files = defect_imgs + bg_imgs
    random.shuffle(all_files)
    
    split_idx = int(len(all_files) * (1 - val_ratio))
    split_data = {'train': all_files[:split_idx], 'val': all_files[split_idx:]}

    print(f"V17 Pipeline: Total({len(all_files)}), Defect({len(defect_imgs)}), BG({len(bg_imgs)})")

    for split, files in split_data.items():
        img_dst, lbl_dst = output_root / split / 'images', output_root / split / 'labels'
        os.makedirs(img_dst, exist_ok=True); os.makedirs(lbl_dst, exist_ok=True)
        
        print(f"Processing {split} split...")
        for img_path in tqdm(files):
            lbl_path = img_path.parent.parent / "labels" / f"{img_path.stem}.txt"
            shutil.copy(str(img_path), str(img_dst / img_path.name))
            sanitize_and_save_labels(str(lbl_path), str(lbl_dst), img_path.stem)
            
            if split == 'train':
                for i in range(1, 4):
                    augment_yolo(str(img_path), str(lbl_path), str(img_dst), str(lbl_dst), 
                                 drone_transform, suffix=f"v17_{i}")

    # data.yaml 생성
    yaml_data = {
        'path': '/content/refined_dataset', 
        'train': 'train/images', 
        'val': 'val/images', 
        'names': {0: 'crack'}
        }
    with open(output_root / 'data.yaml', 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False)
    print(f"\nV17 Pipeline Completed! Saved to: {output_root}")

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    # 📥 사용자 제공 신규 데이터셋 경로 반영 (v5i 반영)
    INPUT_DIR = BASE_DIR / "datasets" / "defect_review.v6i.yolov8"
    OUTPUT_DIR = BASE_DIR / "datasets" / "refined_dataset"
    if INPUT_DIR.exists():
        process_dataset(INPUT_DIR, OUTPUT_DIR)
    else:
        print(f"Error: Dataset not found at {INPUT_DIR}")
