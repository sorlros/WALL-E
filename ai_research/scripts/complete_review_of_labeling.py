import os

def prepare_labelimg_review(dataset_dir):
    """
    LabelImg 검수를 위한 환경을 준비합니다.
    1. predefined_classes.txt 생성 (클래스를 0으로 통일했으므로 'defect' 하나만 등록)
    2. 검수 방법 안내 출력
    """
    # 1. predefined_classes.txt 생성
    # LabelImg는 이 파일을 읽어 클래스 이름을 지정합니다.
    classes_path = os.path.join(dataset_dir, "predefined_classes.txt")
    with open(classes_path, 'w', encoding='utf-8') as f:
        f.write("defect\n")
    
    print("="*50)
    print("LabelImg 검수 준비 완료!")
    print(f"클래스 정의 파일 생성됨: {classes_path}")
    print("="*50)
    print("\n[검수 방법]")
    print("1. 터미널(CMD)에서 'labelImg' 명령어를 입력하여 실행하세요.")
    print("   (설치가 안 되어 있다면: pip install labelImg)")
    print(f"2. 'Open Dir' 클릭 -> 데이터셋 폴더 선택")
    print(f"   ({dataset_dir})")
    print(f"3. 'Change Save Dir' 클릭 -> 라벨 폴더 선택 (이미지와 같으면 생략 가능)")
    print("4. 우측 툴바에서 포맷을 [YOLO]로 변경하세요. (중요!)")
    print("5. 단축키 활용:")
    print("   - D: 다음 이미지")
    print("   - A: 이전 이미지")
    print("   - W: 새 박스 그리기")
    print("   - Ctrl + S: 저장")
    print("="*50)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    DATASET_DIR = os.path.normpath(os.path.join(script_dir, "..", "datasets", "merged_dataset", "merged_dataset"))
    prepare_labelimg_review(DATASET_DIR)
