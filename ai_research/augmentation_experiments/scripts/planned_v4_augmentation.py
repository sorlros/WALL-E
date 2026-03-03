import albumentations as A
import cv2
import os
import glob
from tqdm import tqdm
import shutil
import yaml

# ==========================================
# 1. planned_v4.json 기반 증강 파이프라인 정의
# ==========================================
v4_transform = A.Compose([
    A.OneOf([
        A.MotionBlur(blur_limit=(3, 7), p=1.0),
        A.GaussianBlur(blur_limit=(3, 5), p=1.0)
    ], p=0.3),
    A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
    A.ISONoise(color_shift=(0.01, 0.05), intensity=(0.1, 0.5), p=0.3),
    A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=10, p=0.3),
    A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=0.5),
    A.Sharpen(alpha=(0.2, 0.5), lightness=(0.5, 1.0), p=0.5),
    A.Affine( # ShiftScaleRotate 대체 (최신 권장)
        translate_percent={"x": (-0.02, 0.02), "y": (-0.1, 0.1)},
        scale=(1.0, 1.0), # scale_limit 0.0
        rotate=(-5, 5),
        interpolation=cv2.INTER_LINEAR,
        cval=(114, 114, 114), # value: 114 (회색 배경)
        p=0.5
    ),
    A.HorizontalFlip(p=0.5),
    A.Resize(height=640, width=640, p=1.0) # YOLOv11 권장 사이즈
], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))

# ==========================================
# 2. 증강 수행 함수 구현
# ==========================================
def apply_offline_augmentation(src_dir, dest_dir, num_aug_repeats=2):
    print(f"🚀 [V4 Pipeline] 새로운 데이터셋 복사 및 증강 시작...")
    
    # 1. 새 디렉토리로 원본 복사
    if os.path.exists(dest_dir):
        print(f"⚠️ 이미 대상 디렉토리가 존재합니다. 삭제 후 새로 복사합니다: {dest_dir}")
        shutil.rmtree(dest_dir)
    shutil.copytree(src_dir, dest_dir)
    print(f"✅ 원본 데이터 셋 복사 완료: {dest_dir}")
    print("⏳ 데이터 증강을 진행중입니다. 잠시만 기다려주세요...")
    
    # 2. train 폴더 안의 이미지들만 증강 (valid, test는 원본 유지 원칙)
    img_dir = os.path.join(dest_dir, 'train', 'images')
    lbl_dir = os.path.join(dest_dir, 'train', 'labels')
    
    img_files = glob.glob(os.path.join(img_dir, '*.jpg'))
    
    for img_path in tqdm(img_files, desc="Augmenting Train Data"):
        base_name = os.path.basename(img_path).replace('.jpg', '')
        lbl_path = os.path.join(lbl_dir, f"{base_name}.txt")
        
        # 이미지 로드 (RGB 배열)
        image = cv2.imread(img_path)
        if image is None:
            continue
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 라벨 파싱 (YOLO format: class x y w h)
        bboxes = []
        class_labels = []
        if os.path.exists(lbl_path):
            with open(lbl_path, 'r') as f:
                for line in f.readlines():
                    parts = line.strip().split()
                    if len(parts) == 5:
                        class_labels.append(int(parts[0]))
                        bboxes.append([float(p) for p in parts[1:]])
        
        # 반복 횟수(2번)만큼 증강 복제본 생성
        for i in range(num_aug_repeats):
            try:
                # 라벨(bbox)이 없는 백그라운드 이미지 처리
                if len(bboxes) == 0:
                    augmented = v4_transform(image=image, bboxes=[], class_labels=[])
                # 일반 크랙 이미지 처리
                else:
                    augmented = v4_transform(image=image, bboxes=bboxes, class_labels=class_labels)
                
                aug_img = augmented['image']
                aug_bboxes = augmented['bboxes']
                aug_classes = augmented['class_labels']
                
                # 저장할 새 파일 이름 (_aug_1, _aug_2)
                new_basename = f"{base_name}_v4aug_{i+1}"
                new_img_path = os.path.join(img_dir, f"{new_basename}.jpg")
                new_lbl_path = os.path.join(lbl_dir, f"{new_basename}.txt")
                
                # 증강 이미지 저장
                aug_img_bgr = cv2.cvtColor(aug_img, cv2.COLOR_RGB2BGR)
                cv2.imwrite(new_img_path, aug_img_bgr)
                
                # 증강 라벨 저장 (비어있으면 빈 파일로 둠)
                with open(new_lbl_path, 'w') as f:
                    for cls, bbox in zip(aug_classes, aug_bboxes):
                        f.write(f"{cls} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")
                        
            except Exception as e:
                pass

    # data.yaml의 경로 수정 (새로운 경로 인식하도록 절대 경로로 세팅)
    yaml_path = os.path.join(dest_dir, 'data.yaml')
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        data['path'] = dest_dir
        data['train'] = 'train/images'
        data['val'] = 'valid/images'
        data['test'] = 'test/images'
        
        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    print(f"✅ 데이터 증강 완료! 새로운 데이터셋 위치: {dest_dir}")

if __name__ == '__main__':
    src_dataset = "/Users/choi/Desktop/workspace/Wall-E/ai_research/datasets/crack-with-background"
    dest_dataset = "/Users/choi/Desktop/workspace/Wall-E/ai_research/datasets/crack-with-background-v4-aug"
    apply_offline_augmentation(src_dataset, dest_dataset, num_aug_repeats=2)
