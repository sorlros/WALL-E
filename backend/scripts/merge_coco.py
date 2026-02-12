import json
import shutil
import os
import argparse
from pathlib import Path
from datetime import datetime

"""
Script to merge multiple COCO format datasets into a single dataset.
Usage:
    python merge_coco.py --inputs <dir1> <dir2> ... --output <output_dir>

Example:
    python merge_coco.py --inputs ./dataset1/train ./dataset2/train --output ./merged_dataset/train
"""

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def merge_datasets(input_dirs, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Structure for merged data
    merged_data = {
        "info": {
            "description": "Merged Dataset",
            "url": "",
            "version": "1.0",
            "year": datetime.now().year,
            "contributor": "Wall-E",
            "date_created": datetime.now().isoformat()
        },
        "licenses": [],
        "categories": [],
        "images": [],
        "annotations": []
    }
    
    # ID mappings to prevent collisions
    # We will build a unified category list first.
    category_map = {} # old_cat_id -> new_cat_id (per dataset)
    global_categories = {} # name -> new_cat_id
    
    next_image_id = 0
    next_annotation_id = 0
    next_category_id = 0
    
    print(f"Merging {len(input_dirs)} datasets into {output_dir}...")
    
    for idx, input_dir in enumerate(input_dirs):
        input_dir = Path(input_dir)
        annotation_file = input_dir / "_annotations.coco.json"
        
        if not annotation_file.exists():
            print(f"Warning: Annotation file not found in {input_dir}, skipping.")
            continue
            
        print(f"Processing {input_dir}...")
        data = load_json(annotation_file)
        
        # 1. Process Categories
        # Map local category ID to global category ID
        local_cat_map = {} # local_id -> global_id
        
        for cat in data.get('categories', []):
            name = cat['name']
            if name not in global_categories:
                global_categories[name] = next_category_id
                merged_data['categories'].append({
                    "id": next_category_id,
                    "name": name,
                    "supercategory": cat.get('supercategory', 'none')
                })
                next_category_id += 1
            local_cat_map[cat['id']] = global_categories[name]

        # 2. Process Images
        # Copy image and update ID
        local_img_map = {} # local_id -> global_id
        
        for img in data.get('images', []):
            old_id = img['id']
            file_name = img['file_name']
            
            # Handling image path: check logic
            # Roboflow usually puts images next to json
            src_image_path = input_dir / file_name
            
            if not src_image_path.exists():
                print(f"  Warning: Image {file_name} not found.")
                continue
                
            # Create unique filename to avoid collision
            # e.g., dataset1_0001.jpg
            # Or simpler: just use UUID, or prefix with dataset index
            prefix = input_dir.parent.name if input_dir.parent.name else f"d{idx}"
            new_file_name = f"{prefix}_{file_name}"
            
            dst_image_path = output_dir / new_file_name
            shutil.copy2(src_image_path, dst_image_path)
            
            new_id = next_image_id
            local_img_map[old_id] = new_id
            
            new_img_entry = img.copy()
            new_img_entry['id'] = new_id
            new_img_entry['file_name'] = new_file_name
            merged_data['images'].append(new_img_entry)
            
            next_image_id += 1
            
        # 3. Process Annotations
        for ann in data.get('annotations', []):
            old_img_id = ann['image_id']
            old_cat_id = ann['category_id']
            
            if old_img_id not in local_img_map:
                continue # Skip if image was skipped
                
            new_ann = ann.copy()
            new_ann['id'] = next_annotation_id
            new_ann['image_id'] = local_img_map[old_img_id]
            new_ann['category_id'] = local_cat_map.get(old_cat_id, -1) # Fallback?
            
            merged_data['annotations'].append(new_ann)
            next_annotation_id += 1
            
    # Save merged JSON
    save_json(merged_data, output_dir / "_annotations.coco.json")
    print(f"Done! Merged dataset saved to {output_dir}")
    print(f"Total: {len(merged_data['images'])} images, {len(merged_data['annotations'])} annotations.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge COCO datasets.")
    parser.add_argument("--inputs", nargs='+', required=True, help="List of input directories containing _annotations.coco.json")
    parser.add_argument("--output", required=True, help="Output directory")
    
    args = parser.parse_args()
    merge_datasets(args.inputs, args.output)
