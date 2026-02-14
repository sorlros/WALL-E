# 🏗️ Wall-E 데이터베이스 스키마 및 기능 명세서

이 문서는 Supabase (PostgreSQL) 환경에서의 데이터베이스 구조와 Wall-E 드론 점검 서비스의 데이터 처리 요구사항을 정리한 것입니다.

---

## 1. 데이터베이스 스키마 (PostgreSQL)

### 1-1. 사용자 (Users)
사용자 인증은 **Supabase Auth** (`auth.users`)가 담당합니다.
추가적인 사용자 정보(프로필 등)는 `public.profiles` 테이블에서 관리합니다.

#### `public.profiles`
| 컬럼명 | 타입 | 기본값 | 설명 |
| :--- | :--- | :--- | :--- |
| **`id`** | `uuid` (PK) | - | **Foreign Key** (`auth.users.id`). Supabase 인증 ID와 1:1 매칭됩니다. |
| `username` | `text` | - | 사용자 아이디 (화면 표시용). |
| `full_name` | `text` | - | 사용자 실명. |
| `avatar_url` | `text` | `NULL` | 프로필 이미지 URL (Supabase Storage). |
| `created_at` | `timestamptz` | `now()` | 계정 생성 일시. |

---

### 1-2. 미션 (Missions)
드론 비행 또는 점검 세션을 의미합니다.
*(요청사항에 따라 `status` 컬럼은 삭제되었으며, 완료된 미션 정보만 저장하거나 비행 세션의 메타데이터로 활용됩니다.)*

| 컬럼명 | 타입 | 기본값 | 설명 |
| :--- | :--- | :--- | :--- |
| **`id`** | `bigint` (PK) | 자동생성 | 미션 고유 ID. |
| `user_id` | `uuid` (FK) | - | **Foreign Key** (`public.profiles.id`). 미션 수행자. |
| `title` | `text` | - | 미션 제목 (예: "강남 파이낸스 센터 외벽 점검"). |
| `description` | `text` | `NULL` | 미션에 대한 상세 설명. |
| `location_name` | `text` | - | 장소명 (예: "코엑스 동측"). |
| `location_address`| `text` | - | 사용자가 입력한 상세 주소. |
| `captured_at` | `timestamptz` | `now()` | 실제 촬영/데이터 수집 시점. |
| `created_at` | `timestamptz` | `now()` | 데이터 레코드 생성 시점. |

---

### 1-3. 탐지 결과 (Detections)
미션 수행 중 발견된 개별 크랙(Crack) 정보를 저장합니다.
**GPS 좌표**와 **바운딩 박스(Bounding Box)** 정보를 포함합니다.

| 컬럼명 | 타입 | 기본값 | 설명 |
| :--- | :--- | :--- | :--- |
| **`id`** | `bigint` (PK) | 자동생성 | 탐지 고유 ID. |
| `mission_id` | `bigint` (FK) | - | **Foreign Key** (`public.missions.id`). 소속 미션. |
| `image_url` | `text` | - | **원본 이미지**의 Supabase Storage 경로. (박스가 그려지지 않은 깨끗한 원본) |
| `label` | `text` | `'crack'` | 탐지된 결함 종류 (예: "crack", "spalling"). |
| `confidence` | `float` | - | AI 모델의 탐지 신뢰도 (0.0 ~ 1.0). |
| **`bbox`** | `jsonb` | - | 바운딩 박스 좌표 배열: `[x, y, w, h]` (0~1 정규화된 값 권장). |
| `gps_lat` | `float` | `NULL` | 촬영 당시 드론의 위도 (Latitude). |
| `gps_lng` | `float` | `NULL` | 촬영 당시 드론의 경도 (Longitude). |
| `created_at` | `timestamptz` | `now()` | 탐지 시각. |

---

## 2. 기능 명세 및 데이터 흐름

### 2-1. 전체 흐름 (Workflow)
1.  **드론 비행 시작**:
    *   사용자가 앱에서 '미션 시작'을 누르면 DB에 `Missions` 레코드가 생성됩니다.
2.  **실시간 AI 탐지**:
    *   `StreamManager`가 실시간 영상에서 YOLO 모델을 돌립니다.
    *   크랙이 탐지되면 (신뢰도 0.6 이상):
        1.  **원본 이미지 업로드**: 박스를 그리지 않은 원본 프레임을 Supabase Storage에 업로드합니다.
        2.  **DB 저장**: `image_url`과 함께 `bbox` (좌표), `gps` 정보를 DB에 insert 합니다.
3.  **미션 종료**:
    *   비행이 끝나면 `Missions` 정보(종료 시각 등)를 최종 업데이트합니다.

### 2-2. 바운딩 박스 처리 (Bounding Box)
*   **저장 방식**:
    *   이미지 파일에는 박스를 굽지 않고(Drawing X) **원본 그대로** 저장합니다.
    *   대신 박스의 위치 정보(`[x, y, w, h]`)를 `detections` 테이블의 `bbox` 컬럼에 JSON 형태로 저장합니다.
*   **표시 방식 (Frontend)**:
    *   앱/웹에서 이미지를 불러올 때, `bbox` 데이터도 같이 조회합니다.
    *   Flutter의 `CustomPainter`나 Web의 `Canvas`/CSS를 사용하여 이미지 위에 박스를 **동적으로** 그려줍니다.
    *   **장점**: 추후 박스 색상/두께 변경이 자유롭고, 원본 이미지가 보존되어 재분석이 가능합니다.

### 2-3. 위치 정보 (Location)
*   **GPS**: 드론 텔레메트리에서 실시간으로 받아온 위도/경도를 각 탐지 결과(`detections`)에 저장합니다.
*   **장소명**: 미션 전체를 아우르는 장소 정보(`missions.location_name`)는 사용자가 텍스트로 입력합니다.
