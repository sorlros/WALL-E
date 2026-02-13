import json
import os
import shutil
import argparse
import random
import yaml
from pathlib import Path
from tqdm import tqdm

"""
Script to convert COCO JSON format to YOLO TXT format.
Generates a dataset structure compatible with Ultralytics YOLOv8/v11.

Structure:
output_dir/
  data.yaml
  train/
    images/
    labels/
  val/
    images/
    labels/
"""

def convert_bbox(size, box):
    # COCO: [x, y, w, h]
    # YOLO: [x_center, y_center, width, height] normalized
    dw = 1. / size[0]
    dh = 1. / size[1]
    
    # Cast to float just in case
    x = float(box[0])
    y = float(box[1])
    w = float(box[2])
    h = float(box[3])
    
    x = x + w / 2.0
    y = y + h / 2.0
    
    x = x * dw
    w = w * dw
    y = y * dh
    h = h * dh
    return (x, y, w, h)

def coco_to_yolo(input_json, input_images_dir, output_dir, val_split=0.2):
    input_images_dir = Path(input_images_dir)
    output_dir = Path(output_dir)
    
    # Load COCO JSON
    with open(input_json, 'r') as f:
        data = json.load(f)
        
    # Force map all categories to 'crack' (ID 0)
    categories = {cat['id']: 'crack' for cat in data['categories']}
    cat_id_to_yolo_id = {cat_id: 0 for cat_id in categories.keys()}
    yolo_names = ['crack']
    
    # Group annotations by image
    img_to_anns = {img['id']: [] for img in data['images']}
    for ann in data['annotations']:
        img_to_anns[ann['image_id']].append(ann)
        
    images = data['images']
    random.shuffle(images)
    
    # Split train/val
    split_idx = int(len(images) * (1 - val_split))
    train_imgs = images[:split_idx]
    val_imgs = images[split_idx:]
    
    datasets = {'train': train_imgs, 'val': val_imgs}
    
    print(f"Converting {len(images)} images to YOLO format...")
    print(f"Train: {len(train_imgs)}, Val: {len(val_imgs)}")
    
    for split, split_images in datasets.items():
        # Create directories
        (output_dir / split / 'images').mkdir(parents=True, exist_ok=True)
        (output_dir / split / 'labels').mkdir(parents=True, exist_ok=True)
        
        for img_info in tqdm(split_images, desc=f"Processing {split}"):
            file_name = img_info['file_name']
            src_img_path = input_images_dir / file_name
            
            if not src_img_path.exists():
                print(f"Warning: Image not found {src_img_path}")
                continue
                
            # Copy image
            dst_img_path = output_dir / split / 'images' / file_name
            shutil.copy2(src_img_path, dst_img_path)
            
            # Create Label File
            label_name = Path(file_name).stem + ".txt"
            label_path = output_dir / split / 'labels' / label_name
            
            w = img_info['width']
            h = img_info['height']
            
            with open(label_path, 'w') as lf:
                anns = img_to_anns.get(img_info['id'], [])
                for ann in anns:
                    cat_id = ann['category_id']
                    bbox = ann['bbox'] # x,y,w,h
                    
                    yolo_bbox = convert_bbox((w, h), bbox)
                    yolo_class = cat_id_to_yolo_id[cat_id]
                    
                    # class x_center y_center width height
                    lf.write(f"{yolo_class} {yolo_bbox[0]:.6f} {yolo_bbox[1]:.6f} {yolo_bbox[2]:.6f} {yolo_bbox[3]:.6f}\n")

    # Create data.yaml
    yaml_content = {
        'path': str(output_dir.absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'names': {i: name for i, name in enumerate(yolo_names)}
    }
    
    msg_names = {i: name for i, name in enumerate(yolo_names)} # for print
    
    with open(output_dir / 'data.yaml', 'w') as f:
        yaml.dump(yaml_content, f, sort_keys=False)
        
    print(f"\nConversion complete. Dataset saved to {output_dir}")
    print(f"Classes: {msg_names}")
    print(f"data.yaml created.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert COCO to YOLO")
    parser.add_argument("--json", required=True, help="Path to _annotations.coco.json")
    parser.add_argument("--images", required=True, help="Directory containing images")
    parser.add_argument("--output", required=True, help="Output directory for YOLO dataset")
    parser.add_argument("--val_split", type=float, default=0.2, help="Validation split ratio")
    
    args = parser.parse_args()
    coco_to_yolo(args.json, args.images, args.output, args.val_split)
