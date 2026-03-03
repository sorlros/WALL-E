import cv2
import json
import os
import glob
from collections import Counter
from pathlib import Path
#
def audit_dataset(dataset_path):
    print(f"Auditing dataset at: {dataset_path}")
    
    # 1. Check Image Files
    image_paths = glob.glob(os.path.join(dataset_path, "*.jpg"))
    print(f"Total image files: {len(image_paths)}")
    
    corrupt_images = []
    shapes = []
    
    for img_path in image_paths:
        try:
            img = cv2.imread(img_path)
            if img is None:
                corrupt_images.append(img_path)
            else:
                shapes.append(img.shape)
        except Exception:
            corrupt_images.append(img_path)
            
    if corrupt_images:
        print(f"WARNING: {len(corrupt_images)} corrupt images found: {corrupt_images}")
    else:
        print("Image integrity check: PASSED")
        
    # Check consistency of shapes
    shape_counts = Counter(shapes)
    print(f"Image shapes found: {shape_counts}")
    if len(shape_counts) > 1:
        print("WARNING: Images have inconsistent sizes.")
        
    # 2. Check Annotations
    ann_file = os.path.join(dataset_path, "_annotations.coco.json")
    if not os.path.exists(ann_file):
        print("ERROR: Annotation file not found!")
        return
        
    with open(ann_file, 'r') as f:
        data = json.load(f)
        
    registered_images = {img['id'] for img in data['images']}
    # Check Class Consistency (New)
    categories = {cat['id']: cat['name'] for cat in data.get('categories', [])}
    print(f"Categories defined in JSON: {categories}")
    
    category_ids = [ann['category_id'] for ann in data['annotations']]
    unique_categories = Counter(category_ids)
    print(f"Classes found in annotations (ID: Count): {unique_categories}")
    
    if len(unique_categories) > 1:
        print("WARNING: Multiple classes detected!")
        for cat_id, count in unique_categories.items():
            name = categories.get(cat_id, "Unknown")
            print(f"  - ID {cat_id} ({name}): {count} annotations")
    elif len(unique_categories) == 1:
        cat_id = list(unique_categories.keys())[0]
        name = categories.get(cat_id, "Unknown")
        print(f"Class consistency check: PASSED. All annotations belong to ID {cat_id} ({name}).")
        
    annotated_images = {ann['image_id'] for ann in data['annotations']}
    
    # Check for images without annotations
    missing_annotations = registered_images - annotated_images
    if missing_annotations:
        print(f"WARNING: {len(missing_annotations)} images have no annotations (background images).")
    else:
        print("Annotation check: All images have at least one annotation.")
        
    # Check for file matching
    registered_filenames = {img['file_name'] for img in data['images']}
    disk_filenames = {os.path.basename(p) for p in image_paths}
    
    missing_on_disk = registered_filenames - disk_filenames
    orphan_files = disk_filenames - registered_filenames
    
    if missing_on_disk:
        print(f"WARNING: {len(missing_on_disk)} files listed in JSON are missing from disk.")
    if orphan_files:
        print(f"WARNING: {len(orphan_files)} files on disk are not in JSON.")
        
    if not missing_on_disk and not orphan_files:
        print("File matching check: PASSED (JSON matches Disk perfectly)")

if __name__ == "__main__":
    audit_dataset("/Users/choi/Desktop/workspace/Wall-E/ai_research/datasets/merged_dataset")
