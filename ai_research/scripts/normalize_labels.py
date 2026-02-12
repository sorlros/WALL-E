import os
from glob import glob
from tqdm import tqdm

def normalize_labels(base_dir):
    """
    모든 라벨 파일의 클래스 인덱스를 0으로 통일합니다.
    (사용자 요청: defect 단일 클래스)
    """
    label_files = glob(os.path.join(base_dir, '**', 'labels', '*.txt'), recursive=True)
    
    print(f"Normalizing {len(label_files)} label files...")
    
    for lbl_path in tqdm(label_files):
        if not os.path.isfile(lbl_path):
            continue
            
        with open(lbl_path, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            parts = line.split()
            if parts:
                # 첫 번째 원소(클래스 인덱스)를 '0'으로 변경
                parts[0] = '0'
                new_lines.append(" ".join(parts) + "\n")
        
        with open(lbl_path, 'w') as f:
            f.writelines(new_lines)

if __name__ == "__main__":
    # 스크립트 위치 기준으로 경로 설정
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    AI_RESEARCH_DIR = os.path.dirname(SCRIPT_DIR)
    DATASET_DIR = os.path.join(AI_RESEARCH_DIR, "datasets", "crack_yolo")

    if os.path.exists(DATASET_DIR):
        print(f"Normalizing labels in: {DATASET_DIR}")
        normalize_labels(DATASET_DIR)
        print("Label normalization completed successfully!")
    else:
        print(f"Error: Directory {DATASET_DIR} not found.")
