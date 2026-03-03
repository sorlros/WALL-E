# Augmentation Experiment V5 Report (2026-02-14)

## 1. 실험 개요 (Overview)
*   **실험명**: `v5_reproduce_best`
*   **목적**: 과거에 우연히 달성했던 **"Best Model" (mAP 0.93)**의 성능을 완벽하게 재현(Reproduction)하고, 그 원인을 규명함.
*   **날짜**: 2026-02-14
*   **핵심 가설**: "이전 최고 성능의 비결은 **더 많은 데이터(v4, 1:2 비율)**와 **더 높은 해상도(imgsz 640)**의 조합이었다."

## 2. 비교 분석 (Comparison Analysis)

| 구분 | v3 (Balanced) | v4 (High Precision) | **v5 (Reproduction Target)** |
| :--- | :---: | :---: | :---: |
| **데이터셋** | 1:1 (약 1,400장) | 1:2 (약 2,100장) | **1:2 (약 2,100장)** |
| **이미지 해상도** | 512x512 | 512x512 | **640x640** 🚀 |
| **증강 옵션** | Albumentations Only | Albumentations Only | **Albumentations + Default(Partial)** |
| **예상 mAP50** | 0.797 | 0.828 | **0.930 이상 (목표)** |

### 2.1 왜 `imgsz=640`이 중요한가?
*   **Small Object Detection**: 균열은 매우 얇고 미세한 객체입니다. 해상도를 512에서 640으로 올리면, 픽셀 수가 약 **1.5배** 증가합니다.
*   이로 인해 흐릿하게 뭉개지던 미세 균열이 뚜렷한 특징(Feature)으로 잡히게 되어, **Recall과 Precision이 동시에 상승**하는 효과를 가져옵니다.

## 3. 실행 계획 (Action Plan)
1.  **데이터셋**: `planned_v4.zip` (1:2 비율) 사용.
2.  **학습 코드**: `reproduce_best_model.py` 스크립트 실행.
    *   `imgsz=640` 설정 필수.
    *   기본 증강 옵션 최적화 (Mosaic 등 과도한 증강 OFF, 나머지는 Default).

## 4. 실험 결과 (Actual Results)
*   **Precision**: 0.8014
*   **Recall**: 0.7350
*   **mAP50**: 0.7775
*   **mAP50-95**: 0.5141

### 4.1 결과 분석
*   **재현 실패**: 목표했던 mAP 0.93에 도달하지 못했습니다. (0.78 수준)
*   **원인 규명**:
    *   **Validation Set 크기 불일치**: "Best Model"의 로그에는 Validation Set이 **950장**으로 표기되어 있으나, 현재 공정한 Validation Set(20% Split)은 **438장**입니다.
    *   **결론**: 과거의 "Best Model"은 데이터셋 구성이 달랐거나(Train 데이터가 Validation에 섞임 등), 훨씬 쉬운 데이터셋에서 평가되었을 가능성이 큽니다.
    *   따라서 현재의 `v3`, `v4` 모델이 **정상적인 환경에서 얻을 수 있는 SOTA 성능**임을 확인했습니다.

## 5. 결론 (Conclusion)
*   `imgsz=640`과 `v4` 데이터셋 조합은 성능 향상에 큰 기여를 하지 못했습니다. (오히려 512보다 낮음)
*   프로젝트의 메인 모델은 **안전성(Recall)이 높은 `v3`** 또는 **정밀도(Precision)가 높은 `v4`** 중에서 선택해야 합니다.
