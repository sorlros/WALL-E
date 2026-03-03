# Wall-E Project: AI Crack Detection Model Final Report (2026-02-14)

## 1. 프로젝트 개요 및 필요성 (Project Overview & Necessity)

### 1.1 프로젝트 목표
*   **목표**: 드론 및 모바일 카메라로 촬영된 구조물 이미지에서 **미세한 균열(Crack)**을 실시간으로 탐지하는 경량 AI 모델 개발.
*   **타겟 디바이스**: 엣지 디바이스 (Edge Device) 구동을 고려한 최적화 모델.

### 1.2 AI 모델 도입의 당위성 (Why AI?)
1.  **Safety (안전성 확보)**: 육안 검사가 어려운 고층/위험 지역을 드론으로 대체하여 작업자의 안전을 보장.
2.  **Efficiency (효율성 증대)**: 방대한 분량의 점검 영상을 사람이 일일이 확인하는 비효율을 제거하고, 자동화를 통해 검사 시간을 획기적으로 단축.
3.  **Objectivity (객관성 유지)**: 검사원 개인의 컨디션이나 숙련도에 의존하지 않고, 일관된 기준(SOTA Object Detection Model)으로 결함을 진단.

---

## 2. 모델 및 학습 방법론 (Model & Methodology)

### 2.1 Base Model: YOLOv11n (Nano)
*   **선정 이유**:
    *   **속도(Speed)**: 실시간(Real-time) 스트리밍 분석이 가능하도록 가장 가벼운 Nano 모델 채택.
    *   **성능(Performance)**: 이전 YOLO 버전(v8, v5) 대비 동일 파라미터 수에서 더 높은 mAP를 기록.
    
### 2.2 학습 전략: 전이 학습 (Transfer Learning)
*   **Pre-trained Weight 사용**: `yolo11n.pt` (COCO 데이터셋 사전 학습 모델)
*   **이유**:
    *   **데이터 부족 해결**: 균열 데이터셋의 규모가 상대적으로 작기 때문에(수천 장 수준), 대규모 데이터셋에서 학습된 모델의 **Feature Extractor(특징 추출기)** 능력을 빌려옴.
    *   **파인 튜닝 (Fine-Tuning)**: 초기 가중치는 고정(Freeze)하거나 낮은 Learning Rate로 미세 조정하여, 모델이 '균열'이라는 특정 객체에 빠르게 적응하도록 유도.
    이 과정을 통해 Pre-trained Weight가 망가지지않게 보호

    warmup_epochs: 3.0      # 처음 3 epoch 동안은
    warmup_momentum: 0.8    # 천천히 학습하고
    warmup_bias_lr: 0.1     # Learning Rate를 낮게 하여 예열함

---

## 3. 데이터 증강 전략 (Data Augmentation Strategy)

### 3.1 핵심 철학: "Planned Augmentation" (계획된 증강)
*   YOLO의 기본(Online) 증강 기능(Mosaic, Mixup 등)을 끄고, **Albumentations** 라이브러리를 사용해 정교하게 사전 처리된(Pre-processed) 데이터셋을 구축함.
*   **이유**: 균열은 **형태(Shape)**와 **명암(Contrast)** 정보가 매우 중요하므로, 무작위 왜곡(Random Distortion)보다는 **균열의 특징을 강화**하거나 **현장의 악조건을 시뮬레이션**하는 방향으로 증강을 설계함.

### 3.2 주요 증강 기법
1.  **CLAHE (Contrast Limited Adaptive Histogram Equalization)**:
    *   국소적인 대비를 향상시켜 **희미한 균열을 뚜렷하게** 만듦. (탐지 성능 향상의 핵심 요인)
2.  **Sharpen**:
    *   균열의 경계선을 날카롭게 강조.
3.  **Blur (Motion/Gaussian)** & **Noise (ISO)**:
    *   드론 비행 중 발생할 수 있는 흔들림이나 저조도 노이즈 환경을 시뮬레이션하여 모델의 **강건성(Robustness)** 확보.
4.  **Geometric Transforms (Rotate/Flip)**:
    *   다양한 각도의 균열을 학습하기 위한 기하학적 변환.

---

## 4. 실험 히스토리 및 결과 (Experiments History)

### Phase 1: Pure Augmentation (v1, v2)
*   **전략**: 원본 이미지를 제외하고, 강하게 증강된 이미지만으로 학습.
*   **결과**:
    *   **Precision (정밀도) 높음**: 0.637
    *   **Recall (재현율) 매우 낮음**: 0.479
*   **실패 원인**: 모델이 '과하게 뚜렷한(CLAHE 처리된)' 균열에만 적응하여, 오히려 **평범하고 쉬운 균열을 놓치는 과적합(Over-adaptation)** 발생.

### Phase 2: Mixed Strategy (v3) - **★ 선정된 모델**
*   **전략**: **원본(Original) : 증강(Augmented) = 1 : 1** 혼합.
*   **가설**: "원본 데이터가 중심(Recall)을 잡아주고, 증강 데이터가 예리함(Precision)을 더할 것이다."
*   **결과**:
    *   **mAP50**: **0.797** (대폭 상승)
    *   **mAP50-95**: **0.595** (박스 위치 정확도 매우 우수)
    *   **Recall**: **0.769** (정상 궤도 회복)
    *   **Precision**: **0.783**
*   **성과**: 놓치는 균열이 현저히 줄어들며, 가장 균형 잡힌 성능을 보임.

### Phase 3: High-Augmentation Ratio (v4)
*   **전략**: **원본 : 증강 = 1 : 2** 비율로 증강 데이터 비중 확대.
*   **결과**:
    *   **Precision**: **0.851** (최고 기록)
    *   **Recall**: 0.743 (v3 대비 소폭 하락)
    *   **mAP50**: **0.828**
    *   **mAP50-95**: 0.566 (v3 대비 소폭 하락)
*   **분석**: 정밀도는 매우 높아졌으나, 원본 비율이 줄어들며 재현율(Recall)과 mAP50-95(정밀 위치 추정)가 소폭 감소함.

### Phase X: "Best Model" (wall_e_yolo11n7) - **★ 성능 미스터리**
*   **출처**: 사용자 제공 이미지 (`runs/detect/wall_e_yolo11n7`)
*   **결과**: mAP50 **0.93**, mAP50-95 **0.725** (압도적)
*   **의문점 (Discrepancy)**:
    *   사용자가 제공한 이미지 속 **Validation Set 크기는 950장**입니다.
    *   하지만 현재 v4 데이터셋의 Validation Set 크기는 **438장** (2,187장의 20%)입니다.
*   **결론**: "Best Model"은 **전혀 다른 데이터셋** (아마도 원본+증강 전체를 Validation으로 사용했거나, 더 쉬운 데이터셋)에서 평가되었을 가능성이 매우 높습니다. 따라서 **0.93이라는 점수는 현재 기준으로는 달성 불가능한 점수일 수 있습니다.**

### Phase 4: v5 Reproduction (v5_best_repro)
*   **전략**: v4 데이터셋(1:2) + `imgsz=640` + 기본 증강 일부 허용 (Best Model 재현 시도)
*   **결과**:
    *   **Precision**: 0.801
    *   **Recall**: 0.735
    *   **mAP50**: 0.778
    *   **mAP50-95**: 0.514
*   **분석**:
    *   v4 (mAP 0.828)보다 오히려 성능이 떨어짐.
    *   `imgsz=640`이 오히려 과적합을 유발했거나, 최적화가 덜 되었을 수 있음.
    *   **"Best Model"의 0.93은 재현되지 않음.** (데이터셋 구성 차이가 원인으로 추정됨)

---

## 5. 종합 분석 및 고찰 (Conclusion & Discussion)

### 5.1 모델 성능 비교 (Final Comparison)

| Model | mAP50 | mAP50-95 | Precision | Recall | 비고 |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **v3** (1:1) | 0.797 | **0.595** | 0.783 | **0.769** | **Safety Pick (Best Recall)** ✅ |
| **v4** (1:2) | **0.828** | 0.566 | **0.851** | 0.743 | **Efficiency Pick (Best Precision)** |
| **v5** (Repro) | 0.778 | 0.514 | 0.801 | 0.735 | 재현 실패 (데이터셋 불일치 추정) |
| *Best (Past)* | *0.930* | *0.725* | *0.895* | *0.875* | *Val Set=950장 (비교 불가)* |

### 5.2 최종 결론 및 제언
"Best Model"의 지표(0.93)는 **평가 데이터셋(Validation Set)의 차이(950장 vs 438장)**에서 기인한 것으로 보입니다. 현재 공정한 데이터셋으로 평가했을 때 가장 우수한 모델은 **v3**와 **v4**입니다.

*   **Safety (안전성)**: 균열을 놓치지 않는 것이 중요하다면 **`v3` (1:1 Mix)** 사용을 권장합니다.
*   **Efficiency (효율성)**: 오탐을 줄이고 싶다면 **`v4` (1:2 Mix)** 사용을 권장합니다.

**추천: `v3_mixed_original` 모델 배포 (Reason: Recall Priority)**

### 5.2 Precision vs Recall 트레이드오프
*   `v4` 모델은 **정밀도(Precision)**가 높아 오탐(False Alarm)이 적어 사용자 피로도가 낮을 것입니다.
*   `v3` 모델은 **재현율(Recall)**이 높아 실제 균열을 놓칠 확률이 가장 적습니다.

### 5.2 최종 모델 선정: v3 (1:1 Mix)
*   **안전 진단(Safety Inspection)**이라는 프로젝트의 본질을 고려할 때, **"가짜 알람이 좀 울리더라도, 실제 위협(균열)을 놓치지 않는 것"**이 훨씬 중요합니다.
*   따라서, Recall이 가장 우수한 **`v3_mixed_original` 모델**을 최종 배포 모델로 선정합니다.

### 5.3 향후 발전 방향 (Future Work)
1.  **현장 데이터 피드백 루프 (Data Loop)**: 실제 현장에서 오탐/미탐 사례를 수집하여 `v3` 모델을 지속적으로 재학습(Fine-tuning).
2.  **Hard Negative Mining**: 모델이 헷갈려 하는 배경(전선, 그림자 등) 이미지를 집중적으로 수집하여 오탐률 개선.
3.  **모델 경량화 심화**: 추후 모바일 엣지(NPU) 탑재 시, Quantization(양자화) 등을 통해 속도 추가 확보.

---
**작성자**: Choi (AI Engineer)
**작성일**: 2026-02-14
