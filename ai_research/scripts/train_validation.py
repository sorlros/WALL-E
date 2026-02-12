import os
import random
import shutil
from glob import glob
from tqdm import tqdm

def split_dataset(base_dir, train_ratio=0.8):
    """
    datasets/crack_yolo 내부의 images와 labels를 8:2로 나눕니다.
    구조:
    base_dir/
        images/
        labels/
    결과:
    base_dir/
        train/
            images/
            labels/
        val/
            images/
            labels/
    """
    img_dir = os.path.join(base_dir, 'images')
    lbl_dir = os.path.join(base_dir, 'labels')

    # 모든 이미지 파일 목록 가져오기
    img_files = glob(os.path.join(img_dir, '*.*'))
    img_files = [f for f in img_files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    # 랜덤하게 섞기
    random.seed(42) # 재현성을 위해 시드 고정
    random.shuffle(img_files)

    # 분할 지점 계산
    split_idx = int(len(img_files) * train_ratio)
    train_imgs = img_files[:split_idx]
    val_imgs = img_files[split_idx:]

    # 출력 디렉토리 생성
    for split in ['train', 'val']:
        os.makedirs(os.path.join(base_dir, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(base_dir, split, 'labels'), exist_ok=True)

    def move_files(files, split_name):
        print(f"Moving {len(files)} files to {split_name}...")
        for img_path in tqdm(files):
            file_name = os.path.basename(img_path)
            base_name = os.path.splitext(file_name)[0]
            lbl_path = os.path.join(lbl_dir, base_name + '.txt')

            # 대상 경로 설정
            dst_img = os.path.join(base_dir, split_name, 'images', file_name)
            dst_lbl = os.path.join(base_dir, split_name, 'labels', base_name + '.txt')

            # 파일 이동
            if os.path.exists(img_path):
                shutil.move(img_path, dst_img)
            
            if os.path.exists(lbl_path):
                shutil.move(lbl_path, dst_lbl)
            else:
                print(f"Warning: Label not found for {file_name}")

    # 파일 이동 실행
    move_files(train_imgs, 'train')
    move_files(val_imgs, 'val')

    # 기존 빈 폴더 삭제 (선택 사항)
    # os.rmdir(img_dir)
    # os.rmdir(lbl_dir)

if __name__ == "__main__":
    # 스크립트 위치 기준으로 경로 설정
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    AI_RESEARCH_DIR = os.path.dirname(SCRIPT_DIR)
    DATASET_DIR = os.path.join(AI_RESEARCH_DIR, "datasets", "crack_yolo")

    if os.path.exists(DATASET_DIR):
        print(f"Splitting dataset in: {DATASET_DIR}")
        split_dataset(DATASET_DIR)
        print("Dataset split completed successfully!")
    else:
        print(f"Error: Directory {DATASET_DIR} not found.")
