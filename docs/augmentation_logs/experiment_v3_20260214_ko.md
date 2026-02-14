# Augmentation Experiment V3 Report (2026-02-14)

## 1. 실험 개요 (Overview)
*   **실험명**: `planned_v3_original_mixed`
*   **목적**: `planned_v2` 실험에서 확인된 **낮은 재현율(Low Recall) 문제 해결**
*   **날짜**: 2026-02-14
*   **담당**: Choi (AI Engineer)

## 2. 문제 정의 (Problem Definition)
### `planned_v2` 결과 분석 (Epoch 39 Early STOP)
*   **Precision (정밀도)**: 0.637 (Good) - CLAHE/Sharpen으로 균열 특징이 뚜렷해짐.
*   **Recall (재현율)**: 0.479 (Bad) - 실제 균열의 절반 이상을 놓침.
*   **원인**: 강한 증강(Augmentation)만 학습하여, 오히려 **평범하고 쉬운 균열(Normal Crack)**을 인식하지 못하는 현상 발생 (Over-adaptation to hard cases).

## 3. 해결 전략 (Hypothesis & Strategy)
**"원본 데이터(Original)와 증강 데이터(Augimented)를 1:1로 섞어 학습하면, 정밀도와 재현율을 모두 잡을 수 있을 것이다."**

*   **데이터 구성**:
    1.  **Original (729장)**: 원본 이미지 (Resize 512x512만 적용) -> **Baseline 확보 (Recall 향상)**
    2.  **Augmented (729장)**: `planned_v2`와 동일한 변환 (Blur, Noise, CLAHE, Sharpen 등) -> **Robustness 확보 (Precision 향상)**
    *   **총 데이터셋**: 약 1,458장

## 4. 변경 사항 (Changes)
### Configuration (`planned_v3.json`)
*   `include_originals`: `true` (New Flag)
*   `transforms`: `planned_v2`와 동일 (CLAHE, Sharpen, Blur, Noise 등 유지)

### Script (`augmentation_template.py`)
*   `include_originals` 플래그가 `true`일 경우, 증강 이미지 생성 외에 **원본 이미지도 리사이징하여 함께 저장**하는 로직 추가.
*   `split_dataset` 함수가 늘어난 데이터셋(1458장)을 처리하도록 수정.

## 5. 예상 결과 (Expected Outcome)
*   **Recall**: 0.479 -> **0.60 이상** (쉬운 균열 탐지 능력 회복)
*   **Precision**: 0.637 수준 유지 (강한 증강 효과 지속)
*   **mAP50**: 0.51 -> **0.60 이상** 상승 기대

## 6. 실행 계획 (Action Plan)
1.  `augmentation_template.py` 수정 (원본 포함 로직 구현)
2.  `planned_v3.json`으로 증강 실행
3.  자동 생성된 `data.yaml` 및 `hyp.yaml`(증강 끄기)로 Colab 학습 진행
40. 3.  자동 생성된 `data.yaml` 및 `hyp.yaml`(증강 끄기)로 Colab 학습 진행

## 7. 실험 결과 (Results) - **대성공 (Significant Improvement)**
*   **Precision (정밀도)**: 0.637 -> **0.783** (+14.6%)
*   **Recall (재현율)**: 0.479 -> **0.769** (+29.0%)
*   **mAP50**: 0.510 -> **0.797** (+28.7%)
*   **mAP50-95**: 0.271 -> **0.595** (+32.4%) - 매우 중요 (정밀한 위치 탐지 능력 2배 향상)

### 분석 (Analysis)
1.  **가설 검증 성공**: "원본 + 증강 1:1 혼합" 전략이 유효했음. 원본 데이터가 `Recall`을 대폭 향상시키고, 증강 데이터가 `Precision`을 견인함.
2.  **모델 완성도**: `mAP50`이 0.8에 육박하여, 초기 목표였던 '쓸만한 수준'에 도달함.
3.  **Fitness**: 0.595로, 이전 실험(0.27) 대비 2배 이상 성능 향상.

### 결론 (Conclusion)
이 모델(`v3_mixed_original`)을 **최종 배포 후보(Candidate)로 선정**함. 추가 데이터 수집 전까지 이 모델을 베이스라인으로 사용 권장.
