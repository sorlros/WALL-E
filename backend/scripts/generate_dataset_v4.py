import cv2
import albumentations as A
import argparse
import random
import yaml
import json
import numpy as np
import shutil
from pathlib import Path
from tqdm import tqdm

"""
Script: generate_dataset_v4.py
Purpose: 
1. Load COCO dataset.
2. Split into Train/Val sets.
3. Apply MILD Data Augmentation (Lower probability) to Train set.
4. NO RESIZE applied (Original resolution kept for YOLO letterboxing).
5. Save images and labels in YOLOv8/v11 format.
"""

def get_train_pipeline(grayscale=False):
    pipeline_list = [
        # 1. Camera Effects (Blur/Noise) - Reduced to p=0.1
        A.OneOf([
            A.MotionBlur(p=1, blur_limit=5), # Reduced blur limit
            A.GaussianBlur(p=1, blur_limit=3), # Reduced blur limit
        ], p=0.1),
        
        # 2. Lighting & Sensor Conditions - Reduced to p=0.2
        A.RandomBrightnessContrast(p=0.2, brightness_limit=0.1, contrast_limit=0.1),
        A.ISONoise(p=0.15, intensity=(0.05, 0.2), color_shift=(0.01, 0.03)),
        A.HueSaturationValue(p=0.15, hue_shift_limit=5, sat_shift_limit=10, val_shift_limit=5),
        
        # 3. Enhancement (Contrast & Sharpness) - Reduced to p=0.1
        A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=0.1),
        A.Sharpen(alpha=(0.1, 0.3), lightness=(0.5, 1.0), p=0.1),
        
        # 4. Geometric (Strike Balance) - Reduced shift/rotate
        A.ShiftScaleRotate(
            shift_limit_y=0.05, # 5% shift
            shift_limit_x=0.01, 
            scale_limit=0.0,   
            rotate_limit=3,     # +/- 3 degrees
            p=0.2,
            border_mode=cv2.BORDER_CONSTANT,
            cval=114
        ),
        
        # 5. Horizontal Flip - Kept p=0.5 (Safe)
        A.HorizontalFlip(p=0.5),
        
        # 6. Standardization - NO Resize
        # (YOLO will handle resizing or letterboxing during training)
    ]
    if grayscale:
        pipeline_list.append(A.ToGray(p=1.0))
        
    return A.Compose(pipeline_list, bbox_params=A.BboxParams(format='yolo', label_fields=['category_ids']))

def get_val_pipeline(grayscale=False):
    pipeline_list = [
        # No Resize - keep original quality for evaluation
    ]
    if grayscale:
        pipeline_list.append(A.ToGray(p=1.0))
        
    return A.Compose(pipeline_list, bbox_params=A.BboxParams(format='yolo', label_fields=['category_ids']))

def convert_coco_bbox_to_yolo(size, box):
    # COCO: [x_min, y_min, w, h] -> YOLO: [x_center, y_center, w, h] normalized
    dw = 1. / size[0]
    dh = 1. / size[1]
    
    x = float(box[0]) + float(box[2]) / 2.0
    y = float(box[1]) + float(box[3]) / 2.0
    w = float(box[2])
    h = float(box[3])
    
    x = x * dw
    w = w * dw
    y = y * dh
    h = h * dh
    return [x, y, w, h]

def process_dataset(input_dir, output_dir, multiplier=1, val_split=0.2, grayscale=False):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    # Load COCO JSON
    annotation_file = input_dir / "_annotations.coco.json"
    if not annotation_file.exists():
        print(f"Error: Annotation file not found at {annotation_file}")
        return

    with open(annotation_file, 'r') as f:
        data = json.load(f)
        
    print(f"Loaded {len(data['images'])} images and {len(data['annotations'])} annotations.")

    img_to_anns = {img['id']: [] for img in data['images']}
    for ann in data['annotations']:
        img_to_anns[ann['image_id']].append(ann)
        
    images = data['images']
    random.seed(42)
    random.shuffle(images)
    
    split_idx = int(len(images) * (1 - val_split))
    train_imgs = images[:split_idx]
    val_imgs = images[split_idx:]
    
    print(f"Split: Train {len(train_imgs)} / Val {len(val_imgs)}")
    
    for split in ['train', 'val']:
        (output_dir / split / 'images').mkdir(parents=True, exist_ok=True)
        (output_dir / split / 'labels').mkdir(parents=True, exist_ok=True)

    train_pipeline = get_train_pipeline(grayscale)
    val_pipeline = get_val_pipeline(grayscale)
    
    splits = [('train', train_imgs, train_pipeline, multiplier), 
              ('val', val_imgs, val_pipeline, 1)]

    for split_name, split_images, pipeline, mult in splits:
        print(f"\nProcessing {split_name} set...")
        
        for img_info in tqdm(split_images):
            file_name = img_info['file_name']
            src_img_path = input_dir / file_name
            
            if not src_img_path.exists():
                continue
                
            image = cv2.imread(str(src_img_path))
            if image is None: 
                continue
            
            h, w = image.shape[:2]
            
            anns = img_to_anns.get(img_info['id'], [])
            bboxes = []
            category_ids = []
            
            for ann in anns:
                yolo_bbox = convert_coco_bbox_to_yolo((w, h), ann['bbox'])
                bboxes.append(yolo_bbox)
                category_ids.append(0)
            
            iterations = mult + 1 if split_name == 'train' else 1
            
            for i in range(iterations):
                try:
                    # For original (i=0), use val_pipeline (no augment) to keep it clean
                    current_pipeline = val_pipeline if (i == 0) else pipeline
                    
                    transformed = current_pipeline(image=image, bboxes=bboxes, category_ids=category_ids)
                    
                    aug_img = transformed['image']
                    aug_bboxes = transformed['bboxes']
                    
                    if len(aug_bboxes) == 0 and len(bboxes) > 0:
                         pass
                    
                    if i == 0:
                        out_name = f"{Path(file_name).stem}.jpg"
                    else:
                        out_name = f"aug_{i}_{Path(file_name).stem}.jpg"
                        
                    out_img_path = output_dir / split_name / 'images' / out_name
                    cv2.imwrite(str(out_img_path), aug_img)
                    
                    out_label_path = output_dir / split_name / 'labels' / (out_name.replace('.jpg', '.txt'))
                    
                    with open(out_label_path, 'w') as lf:
                        for bbox in aug_bboxes:
                            xc, yc, bw, bh = bbox
                            xc = max(0, min(1, xc))
                            yc = max(0, min(1, yc))
                            bw = max(0, min(1, bw))
                            bh = max(0, min(1, bh))
                            
                            lf.write(f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
                            
                except Exception as e:
                    print(f"Error processing {file_name}: {e}")

    yaml_content = {
        'path': str(output_dir.absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'names': {0: 'crack'}
    }
    
    with open(output_dir / 'data.yaml', 'w') as f:
        yaml.dump(yaml_content, f, sort_keys=False)
        
    print(f"\nDataset generation complete at {output_dir}")
    print("data.yaml created.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate YOLO Dataset v4 (No Resize, Mild Aug)")
    parser.add_argument("--input", required=True, help="Input directory")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--multiplier", type=int, default=2, help="Number of augmented versions")
    parser.add_argument("--val_split", type=float, default=0.2, help="Validation split ratio")
    parser.add_argument("--grayscale", action="store_true", help="Convert images to grayscale")
    
    args = parser.parse_args()
    process_dataset(args.input, args.output, args.multiplier, args.val_split, args.grayscale)
