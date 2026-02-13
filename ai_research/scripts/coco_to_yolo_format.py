import json
import os
from pathlib import Path

def coco_to_yolo(coco_json_path, output_dir):
    """
    COCO format bounding boxes [x_min, y_min, width, height]
    YOLO format: class_id x_center y_center width height (normalized 0-1)
    """
    with open(coco_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Dictionary to map image_id to image info
    images_info = {img['id']: img for img in data['images']}
    
    # Dictionary to collect annotations for each image
    annotations_by_image = {}
    for ann in data['annotations']:
        img_id = ann['image_id']
        if img_id not in annotations_by_image:
            annotations_by_image[img_id] = []
        annotations_by_image[img_id].append(ann)

    # Process each image
    for img_id, img_info in images_info.items():
        file_name = img_info['file_name']
        img_width = float(img_info['width'])
        img_height = float(img_info['height'])
        
        # Output filename (change .jpg/png to .txt)
        txt_filename = Path(file_name).stem + ".txt"
        txt_path = os.path.join(output_dir, txt_filename)
        
        yolo_lines = []
        
        anns = annotations_by_image.get(img_id, [])
        for ann in anns:
            # User request: unify all classes to index 0
            class_id = 0 
            
            # COCO bbox: [x_min, y_min, width, height]
            # Some values might be strings in the JSON, cast to float
            bbox = [float(x) for x in ann['bbox']]
            x_min, y_min, w, h = bbox
            
            # Convert to YOLO format (center_x, center_y, width, height) normalized
            x_center = (x_min + w / 2) / img_width
            y_center = (y_min + h / 2) / img_height
            w_norm = w / img_width
            h_norm = h / img_height
            
            # Ensure values are within [0, 1]
            x_center = max(0, min(1, x_center))
            y_center = max(0, min(1, y_center))
            w_norm = max(0, min(1, w_norm))
            h_norm = max(0, min(1, h_norm))
            
            yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")
        
        # Write to .txt file
        with open(txt_path, 'w', encoding='utf-8') as f_out:
            f_out.write("\n".join(yolo_lines))

    print(f"Conversion complete. YOLO labels saved to: {output_dir}")

if __name__ == "__main__":
    # Paths configured for the user project
    # JSON 파일 경로 (상대 경로 사용)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    COCO_PATH = os.path.join(script_dir, "..", "datasets", "merged_dataset", "merged_dataset", "_annotations.coco.json")
    # 결과가 저장될 경로 (이미지와 같은 폴더)
    OUTPUT_DIR = os.path.join(script_dir, "..", "datasets", "merged_dataset", "merged_dataset")
    
    if os.path.exists(COCO_PATH):
        coco_to_yolo(COCO_PATH, OUTPUT_DIR)
    else:
        print(f"Error: COCO JSON file not found at {COCO_PATH}")
