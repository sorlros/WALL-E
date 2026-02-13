import json
import shutil
import os
import argparse
import cv2
import numpy as np
import albumentations as A
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

"""
Script to augment a COCO format dataset using Albumentations.
Tailored for Drone Wall Inspection:
- Vertical Motion Blur
- Lighting/Brightness variations
- Sensor Noise
- Minimal Rotation
"""

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def get_augmentation_pipeline():
    return A.Compose([
        # 1. Vertical Motion Blur (Simulate drone moving down)
        # 90 degrees = Vertical can be configured in MotionBlur? 
        # Albumentations MotionBlur doesn't support directional blur easily in older versions, 
        # but we can try simple MotionBlur or assume it's random direction which covers vertical.
        # Actually, best for specific direction is difficult without custom kernel, 
        # so we will use standard MotionBlur and GaussianBlur.
        A.OneOf([
            A.MotionBlur(p=1, blur_limit=7),
            A.GaussianBlur(p=1, blur_limit=5),
        ], p=0.5),
        
        # 2. Lighting & Sensor Conditions
        A.RandomBrightnessContrast(p=0.5, brightness_limit=0.2, contrast_limit=0.2),
        A.ISONoise(p=0.3, intensity=(0.1, 0.5), color_shift=(0.01, 0.05)),
        A.HueSaturationValue(p=0.3, hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=10),
        
        # 3. Enhancement (New: Contrast & Sharpness)
        # CLAHE: Enhances local contrast to reveal subtle cracks in shadows
        A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=0.3),
        # Sharpening: Enhances edges to make thin cracks more visible
        A.Sharpen(alpha=(0.2, 0.5), lightness=(0.5, 1.0), p=0.3),
        
        # 4. Geometric (Stable Flight)
        # ShiftY (Vertical movement simulation - usually covered by simply having data, 
        # but ShiftScaleRotate allows shifting)
        A.ShiftScaleRotate(
            shift_limit_y=0.1, # Shift vertically up to 10%
            shift_limit_x=0.02, # Minimal horizontal shift
            scale_limit=0.0,   # No scaling change (fixed distance)
            rotate_limit=5,    # +/- 5 degrees
            p=0.5,
            border_mode=cv2.BORDER_CONSTANT,
            value=114 # Gray padding
        ),
        
        # 5. Horizontal Flip (Cracks are symmetric)
        A.HorizontalFlip(p=0.5),
        
        # 6. Standardization (Final Resize)
        A.Resize(height=640, width=640, p=1.0),
    ], bbox_params=A.BboxParams(format='coco', label_fields=['category_ids']))

def augment_dataset(input_dir, output_dir, multiplier=1):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    # Setup directories
    images_dir = output_dir 
    images_dir.mkdir(parents=True, exist_ok=True)
    
    annotation_file = input_dir / "_annotations.coco.json"
    if not annotation_file.exists():
        print(f"Error: Annotation file not found at {annotation_file}")
        return

    data = load_json(annotation_file)
    pipeline = get_augmentation_pipeline()
    
    # Prepare output structure (Deep copy generic fields)
    output_data = {k: v for k, v in data.items() if k not in ['images', 'annotations']}
    output_data['images'] = []
    output_data['annotations'] = []
    
    # Index annotations by image_id
    img_to_anns = {}
    for ann in data.get('annotations', []):
        img_id = ann['image_id']
        if img_id not in img_to_anns:
            img_to_anns[img_id] = []
        img_to_anns[img_id].append(ann)
        
    next_img_id = 0
    next_ann_id = 0
    
    print(f"Augmenting dataset from {input_dir} to {output_dir}")
    print(f"Multiplier: {multiplier}x (Total expected: {len(data['images']) * (1 + multiplier)} images)")
    
    for img_info in tqdm(data.get('images', [])):
        img_id = img_info['id']
        file_name = img_info['file_name']
        img_path = input_dir / file_name
        
        if not img_path.exists():
            continue
            
        image = cv2.imread(str(img_path))
        if image is None:
            continue
            
        # Get annotations for this image
        anns = img_to_anns.get(img_id, [])
        bboxes = []
        category_ids = []
        
        for ann in anns:
            # Albumentations COCO format: [x, y, w, h]
            bboxes.append(ann['bbox'])
            category_ids.append(ann['category_id'])
            
        # --- 1. Save Original ---
        new_filename_orig = f"orig_{file_name}"
        cv2.imwrite(str(images_dir / new_filename_orig), image)
        
        new_img_id_orig = next_img_id
        next_img_id += 1
        
        output_data['images'].append({
            "id": new_img_id_orig,
            "file_name": new_filename_orig,
            "width": img_info['width'],
            "height": img_info['height'],
            "date_captured": datetime.now().isoformat()
        })
        
        for i, ann in enumerate(anns):
            new_ann = ann.copy()
            new_ann['id'] = next_ann_id
            new_ann['image_id'] = new_img_id_orig
            output_data['annotations'].append(new_ann)
            next_ann_id += 1
            
        # --- 2. Generate Augmented Versions ---
        for i in range(multiplier):
            try:
                transformed = pipeline(image=image, bboxes=bboxes, category_ids=category_ids)
                aug_image = transformed['image']
                aug_bboxes = transformed['bboxes']
                aug_cat_ids = transformed['category_ids']
                
                # Check if image has valid content (not empty)
                if aug_image is None or aug_image.size == 0:
                    continue

                aug_filename = f"aug_{i}_{file_name}"
                cv2.imwrite(str(images_dir / aug_filename), aug_image)
                
                new_img_id_aug = next_img_id
                next_img_id += 1
                
                output_data['images'].append({
                    "id": new_img_id_aug,
                    "file_name": aug_filename,
                    "width": img_info['width'],
                    "height": img_info['height'],
                    "date_captured": datetime.now().isoformat()
                })
                
                for bbox, cat_id in zip(aug_bboxes, aug_cat_ids):
                    # Filter out tiny boxes that might be artifacts
                    if bbox[2] < 1 or bbox[3] < 1: 
                        continue
                        
                    output_data['annotations'].append({
                        "id": next_ann_id,
                        "image_id": new_img_id_aug,
                        "category_id": cat_id,
                        "bbox": list(bbox),
                        "area": bbox[2] * bbox[3],
                        "iscrowd": 0,
                        "segmentation": [] # BBox aug destroys segmentation polygon unless processed too. Keeping empty for YOLO (boxes only).
                    })
                    next_ann_id += 1
            except Exception as e:
                print(f"Augmentation failed for {file_name} iter {i}: {e}")
                
    # Save Output JSON
    save_json(output_data, output_dir / "_annotations.coco.json")
    print(f"Transformation Complete.")
    print(f"Images: {len(output_data['images'])}")
    print(f"Annotations: {len(output_data['annotations'])}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Augment COCO dataset")
    parser.add_argument("--input", required=True, help="Input directory (containing _annotations.coco.json)")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--multiplier", type=int, default=1, help="Number of augmented versions per original")
    
    args = parser.parse_args()
    augment_dataset(args.input, args.output, args.multiplier)
