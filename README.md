# Paperwork

한국 논문 탐색 + 시간관리 + 집필 보조를 한 번에 제공하는 초기 API 프로젝트입니다.

## 구현된 초기 범위
- 사용자 관심 주제 등록
- 오늘의 추천 논문 조회
- 매일 아침 추천 논문 이메일 발송 잡(시뮬레이션)
- 집필 프로젝트/섹션 진행률 관리
- 진행률 기반 리마인드 생성 및 조회

## 로컬 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

서버 실행 후 문서:
- Swagger UI: `http://127.0.0.1:8000/docs`


## 초보자용 설치 (바탕화면 -> APP -> Paper 경로)
아래는 사용자가 만든 폴더 경로를 그대로 쓰는 방법입니다.

### 1) 터미널에서 폴더로 이동
- macOS/Linux:
```bash
cd ~/Desktop/APP/Paper
```
- Windows PowerShell:
```powershell
cd "C:\Users\신예찬\Desktop\APP\Paper"
```
(현재 사용자 경로 기준 정확한 예시: `C:\Users\신예찬\Desktop\APP\Paper`)

### 2) 코드 가져오기
```bash
git clone <깃허브_레포_URL> .
```

### 3) 가상환경 만들기/켜기
- macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
- Windows PowerShell:
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4) 라이브러리 설치
```bash
pip install -e .[dev]
```

### 5) 서버 실행
```bash
uvicorn app.main:app --reload
```

### 6) 브라우저에서 확인
- `http://127.0.0.1:8000/docs`

## 테스트
```bash
pytest
```

## 주요 API
- `POST /users/topics`
- `PUT /users/email-preferences`
- `GET /papers/recommendations/today?user_id=...`
- `GET /users/daily-digest/preview?user_id=...`
- `POST /jobs/send-daily-paper-email`
- `POST /writing-projects`
- `PATCH /writing-projects/{project_id}/sections/{section_id}`
- `POST /jobs/generate-reminders`
- `GET /users/reminders/today?user_id=...`

## 제품 아이디어 반영 사항
- `오늘의 추천 논문`은 관심 주제 + 최신성 + 집필 미완료 섹션(예: 방법) 우선순위로 정렬됩니다.
- 리마인드는 집필 진행률이 낮은 섹션을 기반으로 실행형 문구를 생성합니다.
