import os
import shutil
import random
import yaml
from pathlib import Path
from tqdm import tqdm

def split_dataset(input_dir, output_dir, train_ratio=0.8, val_ratio=0.2):
    """
    YOLO 포맷의 데이터셋을 Train/Val로 8:2 분할하고 표준 구조로 정리합니다.
    """
    img_dir = os.path.join(input_dir, 'images')
    lbl_dir = os.path.join(input_dir, 'labels')
    
    # 이미지 파일 목록 수집
    if not os.path.exists(img_dir):
        print(f"Error: {img_dir} 폴더를 찾을 수 없습니다.")
        return

    images = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    random.seed(42)
    random.shuffle(images)
    
    total = len(images)
    train_idx = int(total * train_ratio)
    
    splits = {
        'train': images[:train_idx],
        'val': images[train_idx:]
    }
    
    # 기존 출력 폴더 삭제 후 재생성 (깔끔하게 유지)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    print(f"Splitting {total} images into Train ({len(splits['train'])}) and Val ({len(splits['val'])})...")

    # 폴더 구조 생성 및 파일 복사
    for split in splits:
        os.makedirs(os.path.join(output_dir, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, split, 'labels'), exist_ok=True)
        
        for img_name in tqdm(splits[split], desc=f"Copying {split} data"):
            lbl_name = Path(img_name).stem + '.txt'
            
            # 이미지 복사
            src_img = os.path.join(img_dir, img_name)
            dst_img = os.path.join(output_dir, split, 'images', img_name)
            if os.path.exists(src_img):
                shutil.copy2(src_img, dst_img)
            
            # 라벨 복사
            src_lbl = os.path.join(lbl_dir, lbl_name)
            dst_lbl = os.path.join(output_dir, split, 'labels', lbl_name)
            if os.path.exists(src_lbl):
                shutil.copy2(src_lbl, dst_lbl)
            else:
                # 라벨이 없는 경우 빈 파일 생성
                Path(dst_lbl).touch()

    # data.yaml 생성
    yaml_data = {
        'path': os.path.abspath(output_dir).replace('\\', '/'),
        'train': 'train/images',
        'val': 'val/images',
        # 'test': 'test/images', # Test는 미사용
        'names': {
            0: 'defect'
        }
    }
    
    yaml_path = os.path.join(output_dir, 'data.yaml')
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
    
    print(f"\nDataset split complete!")
    print(f"Results saved to: {output_dir}")
    print(f"data.yaml created at: {yaml_path}")

if __name__ == "__main__":
    # 경로 설정
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # 1. 입력 경로: 증강된 데이터가 저장된 폴더 (전 단계의 출력물)
    INPUT_DIR = BASE_DIR / "datasets" / "augmented_yolo_dataset"
    
    # 2. 출력 경로: 최종 학습용 8:2 분할 데이터셋
    OUTPUT_DIR = BASE_DIR / "datasets" / "final_split_dataset"
    
    if INPUT_DIR.exists():
        split_dataset(str(INPUT_DIR), str(OUTPUT_DIR))
    else:
        print(f"Error: 입력 폴더 {INPUT_DIR}를 찾을 수 없습니다.")
        print("전 단계인 coco_augment_to_yolo.py를 먼저 실행하여 데이터를 생성해 주세요.")
