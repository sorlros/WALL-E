# Wall-E 프로젝트 개발 요약 (Walkthrough) - 2026년 02월 20일

본 문서는 2026년 2월 20일에 진행된 Wall-E 프로젝트의 주요 백엔드/프론트엔드 기능 개발 및 아키텍처 개선 사항을 요약한 문서입니다.

---

## 🚀 1. 핵심 개발 기능 (New Features)

### 📸 1.1 수동 이미지 캡처 (Manual Capture FAB)
AI의 자동 탐지 외에도, 사용자가 점검이 필요하다고 판단되는 순간을 직접 촬영하여 기록할 수 있는 기능을 구현했습니다.
* **Backend:** 
  * `POST /missions/{mission_id}/capture` API 엔드포인트 신설.
  * Supabase DB의 `detections` 테이블에 `is_manual` (Boolean) 컬럼을 추가하고 연동.
  * `StreamManager`가 동작 중인 카메라 스레드에서 즉시 최신 프레임을 가져와 저장하는 비동기 로직 구현.
* **Frontend:**
  * 실시간 스트리밍 화면 우측 하단에 수동 캡처용 파란색 `FloatingActionButton(FAB)` 추가.
  * 미션 상세 조회 및 갤러리 화면에서, 기존 AI가 캡처한 이미지와 시각적으로 구분되도록 🟢 **"수동 캡처 🙋‍♂️"** 전용 텍스트 배지 및 초록색 하이라이트 UI 반영.

### 🧠 1.2 MobileNetV3 기반 중복 이미지 필터링 (Re-ID)
기존 YOLO 트래킹 ID 방식의 한계(드론 흔들림으로 인해 같은 균열이 여러 장 중복 저장되는 현상)를 방지하기 위해, 초경량 딥러닝 모델 기반의 재식별(Re-Identification) 파이프라인을 구축했습니다.
* **`ReIDManager` 모듈 신설 (`core/reid_manager.py`)**
  * 약 2.5M 파라미터의 가벼운 `MobileNetV3-small` 구조를 로드.
  * 인터넷이 없는 폐쇄망/엣지 디바이스 환경을 고려하여 캐시가 아닌 **로컬 가중치 파일**(`models/mobilenet_v3_small-047dcff4.pth`)을 직접 캐싱하여 불러오도록 (Offline 모드) 설계.
  * 잘려진 균열 이미지를 입력으로 받아 분류 레이어 없이 통과시켜, 576차원의 특징 벡터(Embedding)를 추출하는 기능 구현.
* **스트리밍 파이프라인 통합 및 튜닝 (`core/stream_manager_ai_only.py`)**
  * 실시간 YOLO 추론 결과(Bounding Box)에 대해 즉각적으로 마진 10%(상하좌우 주변 패턴 스윕)를 덧붙여 Crop.
  * 추출된 임베딩과 최근 50개의 캐시 데이터(`deque`) 간의 코사인 유사도(Cosine Similarity)를 비교.
  * 튜닝된 **임계값 80% (`0.80`)** 이상 일치하면 "중복"으로 판정하여 DB 저장을 무효화(Drop) 처리 (성공률 검증 스크립트 기반 `test_reid.py` 완료).

---

## 🏗️ 2. 아키텍처 및 문서화 (Documentation)

### 📊 2.1 시스템 아키텍처 다이어그램 도입
복잡해진 실시간 3-Track 멀티스레드 스트리밍 파이프라인과 전체 시스템 구성도(클라이언트-백엔드-미디어 서버-DB)를 한눈에 볼 수 있도록 도식화 문서를 작성했습니다.
* **생성 파일:** `docs/system_architecture_kr.md`
* **주요 내용:** 전체 인프라 구성도 및 백엔드의 카메라 수신 ➔ AI 추론 ➔ 인코딩 송출 스레드의 비동기 시퀀스 흐름(Mermaid 형태) 명세화.

### 🚁 2.2 드론 비행 고도화 증강(Augmentation) 계획 수립
드론의 실제 비행 조건(정면 수직 3m 이동)에 맞춰 영상 인식 오탐지(False Positive)를 극한으로 줄이는 머신러닝 데이터 구축 계획을 수립했습니다.
* **초점화된 증강 전략:** Albumentations 기반으로 수평 왜곡은 줄이고, 수직 흔들림(Shift)과 모션 블러(Motion Blur)에 강점을 주는 코드 파이프라인 제안.
* **하드 네거티브 마이닝 (Hard Negative Mining):** 거미줄, 전선, 타일 이음새 등 모델이 헷갈리기 쉬운 장애물 사진(라벨이 빈 Background 파일)을 10~20% 비율로 적극 혼합하는 학습 팁 제안서 완성 및 해당 내용 문서 업데이트(`docs/embedding_reid_plan_kr.md`).

---

## 🔗 3. 배포 및 깃허브 반영 (Git)
현재의 모든 변경점 및 로컬 브랜치의 작업 내용이 정상적으로 Git 레포지토리로 푸시되어 PR 준비를 마쳤습니다.
* **Branch Name:** `gyucheol/manual-capture-and-reid`
* **Commit 요약:** 수동 캡처&MobileNetV3 기반 중복이미지 필터링&최신 아키텍처 문서화
