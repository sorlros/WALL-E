import cv2
import albumentations as A
import os
import glob
import json
from tqdm import tqdm

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

def apply_augmentation(image_path, pipeline, output_dir, img_info, annotations, suffix="", save_original=False):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error reading {image_path}")
        return
        
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w = image.shape[:2]
    
    bboxes = []
    category_ids = []
    
    # Process annotations for this image
    for ann in annotations:
        # Convert COCO to YOLO
        yolo_bbox = convert_coco_bbox_to_yolo((w, h), ann['bbox'])
        bboxes.append(yolo_bbox)
        category_ids.append(0) # Force Class 0
        
    # Apply Pipeline
    try:
        # Pass bboxes/categories if present, or empty lists if supported/matches params
        # Albumentations with BboxParams generally expects these arguments
        augmented = pipeline(image=image, bboxes=bboxes, category_ids=category_ids)
        
        image_aug = augmented['image']
        aug_bboxes = augmented['bboxes']
        
    except Exception as e:
        print(f"Error augmenting {os.path.basename(image_path)}: {e}")
        return

    # Save Image
    base_name = os.path.basename(image_path)
    stem = os.path.splitext(base_name)[0]
    
    # Insert suffix before extension
    name_no_ext, ext = os.path.splitext(base_name)
    aug_filename = f"aug_{name_no_ext}{suffix}{ext}"
    output_path_img = os.path.join(output_dir, aug_filename)
    
    image_aug = cv2.cvtColor(image_aug, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path_img, image_aug)
    
    # Save Label (YOLO format .txt)
    aug_labelname = f"aug_{stem}{suffix}.txt"
    output_path_lbl = os.path.join(output_dir, aug_labelname)
    if aug_bboxes:
        with open(output_path_lbl, 'w') as f:
            for bbox in aug_bboxes:
                x_c, y_c, bw, bh = bbox
                # Safety clip 0-1
                x_c = max(0, min(1, x_c))
                y_c = max(0, min(1, y_c))
                bw = max(0, min(1, bw))
                bh = max(0, min(1, bh))
                
                # FORCE CLASS 0
                f.write(f"0 {x_c:.6f} {y_c:.6f} {bw:.6f} {bh:.6f}\n")

    # Save Original (Resized) if requested
    if save_original:
        # Resize original image and bboxes to target size (512x512 from config usually, but here we assume pipeline has Resize)
        # To be safe and consistent, we use a separate simple resize pipeline or just cv2.resize if no bboxes.
        # BUT, to keep bboxes correct, we should use Albumentations 'Resize' only.
        
        # Helper to get target size from pipeline (hacky but effective)
        target_height, target_width = 512, 512 # Default
        for t in pipeline.transforms:
            if isinstance(t, A.Resize):
                target_height = t.height
                target_width = t.width
                break
                
        resize_transform = A.Compose([
            A.Resize(height=target_height, width=target_width)
        ], bbox_params=A.BboxParams(format='yolo', label_fields=['category_ids']))
        
        try:
            # Original bboxes (converted to YOLO format above)
            # We need to re-convert because they were consumed? No, 'bboxes' list is still valid.
            res = resize_transform(image=image, bboxes=bboxes, category_ids=category_ids)
            orig_resized = res['image']
            orig_bboxes = res['bboxes']
            
            output_path_orig = os.path.join(output_dir, f"orig_{base_name}")
            orig_resized = cv2.cvtColor(orig_resized, cv2.COLOR_RGB2BGR)
            cv2.imwrite(output_path_orig, orig_resized)
            
            output_path_orig_lbl = os.path.join(output_dir, f"orig_{stem}.txt")
            if orig_bboxes:
                with open(output_path_orig_lbl, 'w') as f:
                    for bbox in orig_bboxes:
                        x_c, y_c, bw, bh = bbox
                        # Safety clip
                        x_c = max(0, min(1, x_c))
                        y_c = max(0, min(1, y_c))
                        bw = max(0, min(1, bw))
                        bh = max(0, min(1, bh))
                        f.write(f"0 {x_c:.6f} {y_c:.6f} {bw:.6f} {bh:.6f}\n")
                        
        except Exception as e:
            print(f"Error saving original {base_name}: {e}")

def parse_transforms(transform_list):
    compiled = []
    for t in transform_list:
        name = t['name']
        params = t.get('params', {})
        
        if name in ['OneOf', 'SomeOf', 'Sequential']:
            sub_transforms = parse_transforms(params.get('transforms', []))
            clean_params = {k: v for k, v in params.items() if k != 'transforms'}
            attr = getattr(A, name)
            compiled.append(attr(sub_transforms, **clean_params))
        else:
            for k, v in params.items():
                if isinstance(v, list):
                    params[k] = tuple(v)
            attr = getattr(A, name)
            compiled.append(attr(**params))
    return compiled

def run_experiment(config_path, input_dir, output_dir):
    # Load Config
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    transforms = parse_transforms(config.get('transforms', []))
    pipeline = A.Compose(transforms, bbox_params=A.BboxParams(format='yolo', label_fields=['category_ids']))
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load COCO Annotations
    ann_file = os.path.join(input_dir, "_annotations.coco.json")
    if not os.path.exists(ann_file):
        print(f"Annotation file not found: {ann_file}")
        return
        
    with open(ann_file, 'r') as f:
        coco_data = json.load(f)
        
    # Map Image ID -> Annotations
    img_to_anns = {img['id']: [] for img in coco_data['images']}
    for ann in coco_data['annotations']:
        img_to_anns[ann['image_id']].append(ann)
        
    # Map Filename -> Image Info (to find annotations by filename)
    filename_to_img = {img['file_name']: img for img in coco_data['images']}
        
    image_paths = glob.glob(os.path.join(input_dir, "*.jpg"))
    if not image_paths:
        print(f"No images found in {input_dir}")
        return
    
    print(f"Running experiment: {config.get('experiment_name', 'Unnamed')}")
    print(f"Applying transforms to {len(image_paths)} images...")
    
    # Process Full Dataset
    processed_count = 0
    errors = 0
    
    num_repeats = config.get('num_aug_repeats', 1)
    include_originals = config.get('include_originals', False)
    
    for img_path in tqdm(image_paths):
        fname = os.path.basename(img_path)
        img_info = filename_to_img.get(fname)
        
        if not img_info:
            print(f"Warning: {fname} not found in JSON metadata.")
            continue
            
        annotations = img_to_anns.get(img_info['id'], [])
        
        try:
            for i in range(num_repeats):
                # Add suffix if repeating (start from 0 or 1? 0 is fine, but maybe inconsistent if repeats=1)
                # To keep it simple: if repeats > 1, use suffix `_0`, `_1`. If repeats=1, use no suffix.
                suffix = f"_{i}" if num_repeats > 1 else ""
                
                # Only save original on the first pass
                save_orig = (i == 0) and include_originals
                
                apply_augmentation(img_path, pipeline, output_dir, img_info, annotations, suffix=suffix, save_original=save_orig)
                processed_count += 1
                
        except Exception as e:
            print(f"Error processing {fname}: {e}")
            errors += 1
            
    print(f"\nAugmentation Complete: {processed_count} augmentations processed (repeats={num_repeats}), {errors} errors.")
    
    if errors == 0 and processed_count > 0:
        split_dataset(output_dir, val_split=0.2)
        create_data_yaml(output_dir)
        create_hyp_yaml(output_dir)
        create_zip_archive(output_dir)
    else:
        print("Skipping train/val split due to errors or no data processed.")

def create_data_yaml(output_dir):
    yaml_path = os.path.join(output_dir, "data.yaml")
    train_path = os.path.abspath(os.path.join(output_dir, "train", "images"))
    val_path = os.path.abspath(os.path.join(output_dir, "val", "images"))
    
    content = f"""train: {train_path}
val: {val_path}

nc: 1
names: ['crack']
"""
    with open(yaml_path, 'w') as f:
        f.write(content)
    print(f"Created data.yaml at {yaml_path}")
    
def create_hyp_yaml(output_dir):
    hyp_path = os.path.join(output_dir, "hyp.yaml")
    
    # Standard content disabling most augmentations
    content = """# YOLOv11 Hyperparameters for pre-augmented data
# Disable online augmentations to avoid double-distortion

lr0: 0.01  # initial learning rate (SGD=1E-2, Adam=1E-3)
lrf: 0.01  # final OneCycleLR learning rate (lr0 * lrf)
momentum: 0.937  # SGD momentum/Adam beta1
weight_decay: 0.0005  # optimizer weight decay 5e-4
warmup_epochs: 3.0  # warmup epochs (fractions ok)
warmup_momentum: 0.8  # warmup initial momentum
warmup_bias_lr: 0.1  # warmup initial bias lr
box: 7.5  # box loss gain
cls: 0.5  # cls loss gain (scale with pixels)
dfl: 1.5  # dfl loss gain
pose: 12.0  # pose loss gain
kobj: 1.0  # keypoint obj loss gain
label_smoothing: 0.0  # label smoothing (fraction)
nbs: 64  # nominal batch size

# Augmentation settings (Disabled/Reduced)
hsv_h: 0.0  # image HSV-Hue augmentation (fraction) - DISABLED
hsv_s: 0.0  # image HSV-Saturation augmentation (fraction) - DISABLED
hsv_v: 0.0  # image HSV-Value augmentation (fraction) - DISABLED
degrees: 0.0  # image rotation (+/- deg) - We did this in Albumentations
translate: 0.0  # image translation (+/- fraction) - We did this in Albumentations
scale: 0.0  # image scale (+/- gain) - We did this in Albumentations
shear: 0.0  # image shear (+/- deg)
perspective: 0.0  # image perspective (+/- fraction), range 0-0.001
flipud: 0.0  # image flip up-down (probability)
fliplr: 0.5  # image flip left-right (probability) - OK to keep light flipping
mosaic: 0.0  # image mosaic (probability) - DISABLED (Too strong for cracks)
mixup: 0.0  # image mixup (probability) - DISABLED
copy_paste: 0.0  # segment copy-paste (probability) - DISABLED
"""
    with open(hyp_path, 'w') as f:
        f.write(content)
    print(f"Created hyp.yaml at {hyp_path}")

def create_zip_archive(output_dir):
    import shutil
    
    zip_filename = f"{output_dir}.zip"
    print(f"Creating zip archive: {zip_filename} ...")
    
    # shutil.make_archive(base_name, format, root_dir, base_dir)
    # root_dir: directory to be archived
    # base_dir: directory inside the archive
    
    # We want the zip to contain the folder 'planned_v3' at the root
    parent_dir = os.path.dirname(output_dir)
    base_name = os.path.basename(output_dir)
    
    try:
        shutil.make_archive(output_dir, 'zip', root_dir=parent_dir, base_dir=base_name)
        print(f"Successfully created zip archive at {zip_filename}")
    except Exception as e:
        print(f"Error creating zip archive: {e}")

def split_dataset(data_dir, val_split=0.2):
    print(f"\nStarting Train/Val Split (Val Ratio: {val_split})...")
    import shutil
    import random
    
    # 1. Create Structure
    dirs = ['train', 'val']
    subdirs = ['images', 'labels']
    
    for d in dirs:
        for s in subdirs:
            os.makedirs(os.path.join(data_dir, d, s), exist_ok=True)
            
    # 2. List all images
    images = glob.glob(os.path.join(data_dir, "*.jpg"))
    random.seed(42)
    random.shuffle(images)
    
    val_size = int(len(images) * val_split)
    train_images = images[val_size:]
    val_images = images[:val_size]
    
    print(f"Total: {len(images)} -> Train: {len(train_images)}, Val: {len(val_images)}")
    
    def move_files(file_list, split_name):
        for img_path in tqdm(file_list, desc=f"Moving {split_name}"):
            base_name = os.path.basename(img_path)
            stem = os.path.splitext(base_name)[0]
            label_path = os.path.join(data_dir, f"{stem}.txt")
            
            # Move Image
            dst_img = os.path.join(data_dir, split_name, 'images', base_name)
            shutil.move(img_path, dst_img)
            
            # Move Label if exists
            if os.path.exists(label_path):
                dst_lbl = os.path.join(data_dir, split_name, 'labels', f"{stem}.txt")
                shutil.move(label_path, dst_lbl)
                
    move_files(train_images, 'train')
    move_files(val_images, 'val')
    print("Dataset split completed successfully.")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CONFIG_PATH = os.path.join(BASE_DIR, 'configs', 'planned_v4.json')
    INPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), 'datasets', 'merged_dataset')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs', 'planned_v4')
    
    run_experiment(CONFIG_PATH, INPUT_DIR, OUTPUT_DIR)
