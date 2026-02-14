# 📄 Wall-E 개발 작업 명세서 (2026-02-13)

오늘 진행된 주요 기능 구현, 작업 내용, 사용된 툴 및 발생했던 오류와 해결 과정을 정리한 명세서입니다.

## 1. 🚀 오늘 완료된 주요 작업 (Today's Achievements)

### A. 🔐 사용자 인증 시스템 구현 (Supabase Auth Integration)
- **백엔드**: `FastAPI`와 `supabase-py`를 연동하여 로그인 및 회원가입 API를 구현했습니다. (`backend/api/auth.py`)
- **프론트엔드**: `ApiService`에 인증 로직을 추가하고, `LoginScreen` 및 `SignUpScreen`을 실제 API와 연결했습니다.

### B. �️ Supabase DB 인프라 구축 (Database Setup)
- **환경 설정**: `.env` 파일에 Supabase 프로젝트의 `DATABASE_URL`을 설정하여 PostgreSQL 데이터베이스에 연결했습니다.
- **스키마 자동화**: `SQLAlchemy` ORM 모델을 정의하고, `backend/init_db.py` 스크립트를 통해 `profiles`(사용자), `missions`(작업), `detections`(감지 결과) 테이블을 자동으로 생성했습니다.
- **연결 검증**: `check_db_connection.py`를 작성하여 백엔드 서버와 Supabase 클라우드 DB 간의 실시간 통신 상태를 확인했습니다.

### C. �🔌 포트 충돌 및 리소스 관리 최적화 (Port Conflict Resolution)
- **문제**: 서버 재시작 시 `Address already in use (Port 8000)` 오류가 지속적으로 발생했습니다.
- **원인**: `StreamManager`의 백그라운드 스레드가 `uvicorn` 종료 후에도 포트를 점유하고 있던 현상을 파악했습니다.
- **해결**: `FastAPI`의 `shutdown` 이벤트 핸들러를 사용하여 서버 종료 시 `StreamManager.release()`를 강제 호출하도록 수정했습니다. (`backend/main.py`)

### D. 📱 앱 내비게이션 및 UI 리팩토링 (UI & Navigation Refactoring)
- **레이아웃 수정**: 메인 화면에서 "실시간" 탭을 제거하고, "새 미션"과 "라이브러리", "프로필" 3개 탭 체제로 변경했습니다.
- **사용자 흐름 최적화**: 실시간 영상 스트리밍 UI는 "새 미션" 탭에서 정보를 입력하고 "미션 시작" 버튼을 눌렀을 때만 진입할 수 있도록 사용자 흐름을 강제했습니다.

### E. 🖼️ 갤러리 및 상세 화면 연동 (Gallery Integration)
- **데이터 바인딩**: 미션 목록에서 해당 미션의 최신 감지 이미지를 썸네일로 표시하도록 수정했습니다.
- **상세 화면**: 감지된 균열 이미지들을 그리드 형태로 확인하고, 이미지 경로 버그(URL 슬래시 중복 및 키 명칭 불일치)를 해결했습니다.

---

## 2. 🛠️ 사용된 기술 및 도구 (Tools & Technologies)

| 분류 | 기술 / 툴 | 용도 |
| :--- | :--- | :--- |
| **Backend** | `FastAPI`, `Uvicorn` | 메인 서버 및 API 구축 |
| **Database** | `SQLAlchemy`, `PostgreSQL (Supabase)` | 데이터 저장 및 ORM 관리 |
| **Auth** | `Supabase Auth` | 사용자 인증 및 보안 |
| **AI/Vision** | `YOLOv11 (Ultralytics)`, `OpenCV` | 실시간 균열 감지 및 이미지 처리 |
| **Frontend** | `Flutter (Dart)` | 크로스 플랫폼 앱 UI 구현 |
| **Streaming** | `MJPEG`, `MediaMTX (RTMP/RTSP)` | 실시간 영상 송출 및 스트리밍 |

---

## 3. ⚠️ 오류 해결 과정 (Troubleshooting & Debugging)

### 1) 'Address already in use' (Port 8000)
- **오류 내용**: `uvicorn` 종료 후 즉시 재시작이 불가능한 현상.
- **분석**: `StreamManager` 내부의 `threading.Thread`가 `daemon=True`임에도 불구하고 연결된 리소스를 즉시 해제하지 않아 포트 점유가 유지됨.
- **해결**: `app.on_event("shutdown")`에서 스레드 조인 및 `cap.release()` 명시적 호출.

### 2) Python 모듈 임포트 경로 오류
- **오류 내용**: `ModuleNotFoundError: No module named 'backend'`
- **원인**: `main.py`와 API 모듈 간의 상대/절대 경로 설정 불일치.
- **해결**: 모든 임포트를 `api`, `core`, `db` 등 최상위 패키지 기준으로 통일하고 실행 경로를 `/backend`로 고정.

### 3) 갤러리 이미지 로드 실패
- **오류 내용**: `404 Not Found` 또는 이미지 깨짐 현상.
- **해결**: `image_url` 경로에서 중복된 `/` 제거 및 백엔드의 정적 파일 마운트(`StaticFiles`) 경로 재확인.

---

## 4. 🔗 다음 작업 예정 (Next Steps)
- 이미지 서버를 로컬에서 **Supabase Storage**로 완전히 이전.
- 실시간 감지 시 **GPS 데이터** 연동 및 지도 표시 기능 추가.
- UI 세부 마감 (애니메이션 및 인터랙션 강화).
