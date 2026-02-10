from ultralytics import YOLO
import os
import glob

def test_model():
    # 1. 학습된 최적의 모델 가중치 로드
    # 학습 결과 폴더 내의 best.pt 경로를 지정합니다.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.normpath(os.path.join(script_dir, '../../..', 'runs/detect/crack_detection_v1/weights/best.pt'))
    
    if not os.path.exists(model_path):
        print(f"오류: 모델 파일을 찾을 수 없습니다. 경로를 확인해주세요: {model_path}")
        return

    model = YOLO(model_path)

    # 2. 테스트할 이미지 경로 설정
    # dataset/test/images 폴더에 있는 이미지들 중 하나를 무작위로 고르거나 전체를 테스트합니다.
    test_images_path = os.path.normpath(os.path.join(script_dir, '../dataset/test/images'))
    image_files = glob.glob(os.path.join(test_images_path, "*.jpg"))

    if not image_files:
        print(f"테스트할 이미지가 {test_images_path} 폴더에 없습니다.")
        return

    # 3. 추론(Prediction) 실행
    print(f"총 {len(image_files)}장의 이미지에 대해 테스트를 시작합니다...")
    
    # 첫 번째 이미지 한 장만 테스트해서 결과를 확인해봅니다.
    results = model.predict(source=image_files[0], save=True, conf=0.25)
    
    print("\n" + "="*50)
    print("테스트 완료!")
    print(f"결과 이미지는 다음 폴더에 저장되었습니다: runs/detect/predict")
    print("="*50)

if __name__ == "__main__":
    test_model()
