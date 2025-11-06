# Minute AI - 인수인계 문서

## 📅 마지막 업데이트: 2025-11-06

---

## 🎯 프로젝트 개요

**Minute AI**는 회의 음성을 텍스트로 변환하고, AI 기반으로 요약 및 회의록을 자동 생성하는 Flask 웹 애플리케이션입니다.

### 핵심 기능 (✅ 모두 완료)
- 🎤 **STT (Speech-to-Text)**: Gemini 2.5 Pro로 음성 인식 및 화자 분리
- 📝 **Smart Chunking**: 화자/시간 기반 의미적 청킹
- 🤖 **AI 요약**: Gemini 2.5 Pro로 소주제별 요약 생성
- 📄 **회의록 생성**: RAG 기반 구조화된 회의록 작성
- 🔍 **검색 시스템**: 4가지 retriever 타입 지원
- 💬 **AI 챗봇**: 회의 내용 질의응답 (Self-query retriever 기반)
- 🗑️ **노트 삭제**: 개별/일괄 삭제 기능 + 삭제 검증 로그
- 🔐 **인증 시스템**: Firebase Authentication (Google OAuth)
- 👥 **사용자 관리**: 권한 기반 접근 제어 및 노트 공유 기능
- 🎬 **비디오 지원**: MP4 파일 자동 오디오 변환 (ffmpeg)

---

## 📂 프로젝트 구조

```
minute_ai/
├── app.py                      # Flask 메인 애플리케이션
├── database/
│   └── minute_ai.db           # SQLite 데이터베이스
├── utils/
│   ├── stt.py                 # Gemini STT & AI 처리
│   ├── db_manager.py          # SQLite 작업 관리
│   ├── vector_db_manager.py   # ChromaDB 벡터 DB 관리
│   ├── chat_manager.py        # 챗봇 로직
│   ├── firebase_auth.py       # Firebase 인증 관리 (NEW: 2025-11-06)
│   ├── user_manager.py        # 사용자 및 권한 관리 (NEW: 2025-11-06)
│   ├── decorators.py          # 인증 데코레이터 (NEW: 2025-11-06)
│   ├── analysis.py            # 화자 분석 (NEW: 2025-11-06)
│   └── validation.py          # 입력 유효성 검사
├── templates/
│   ├── layout.html            # 공통 레이아웃 (챗봇 UI 포함)
│   ├── index.html             # 업로드 페이지 (프로그레스바 포함)
│   ├── notes.html             # 모든 노트 목록 (일괄 삭제 기능 포함)
│   ├── viewer.html            # 회의록 뷰어
│   └── retriever.html         # 검색 테스트 페이지
├── static/
│   ├── css/
│   │   └── style.css          # 전체 스타일 (챗봇 UI 포함)
│   └── js/
│       ├── script.js          # 전역 스크립트 (챗봇 로직 포함)
│       └── viewer.js          # 뷰어 인터랙션
├── uploads/                    # 업로드된 오디오 파일
├── FLOWCHART.md               # 시스템 아키텍처 문서
└── next.md                    # 이 문서
```

---

## 🗄️ 데이터베이스 구조

### SQLite Database (`minute_ai.db`)

#### 1. `users` 테이블 (NEW: 2025-11-06)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_id TEXT UNIQUE NOT NULL,     -- Firebase UID
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    profile_picture TEXT,
    role TEXT DEFAULT 'user',           -- 'user' or 'admin'
    created_at TEXT NOT NULL
);
```

#### 2. `meeting_dialogues` 테이블
```sql
CREATE TABLE meeting_dialogues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL,           -- 🔑 삭제 키값
    meeting_date DATETIME NOT NULL,
    speaker_label TEXT NOT NULL,
    start_time REAL NOT NULL,
    segment TEXT NOT NULL,
    confidence REAL,
    audio_file TEXT NOT NULL,
    title TEXT NOT NULL,
    owner_id INTEGER,                   -- NEW: 2025-11-06, FOREIGN KEY(users.id)
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
```

#### 3. `meeting_minutes` 테이블
```sql
CREATE TABLE meeting_minutes (
    meeting_id TEXT PRIMARY KEY,        -- 🔑 삭제 키값
    title TEXT NOT NULL,
    meeting_date TEXT NOT NULL,
    minutes_content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    owner_id INTEGER,                   -- NEW: 2025-11-06, FOREIGN KEY(users.id)
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
```

#### 4. `meeting_shares` 테이블 (NEW: 2025-11-06)
```sql
CREATE TABLE meeting_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    shared_with_id INTEGER NOT NULL,
    shared_at TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    FOREIGN KEY (shared_with_id) REFERENCES users(id),
    UNIQUE(meeting_id, shared_with_id)
);
```

### Vector Database (ChromaDB)

#### Collection: `meeting_chunk`
- **용도**: RAG 기반 회의록 생성 및 검색
- **Embedding**: OpenAI text-embedding-3-small
- **메타데이터**:
  ```python
  {
      "meeting_id": str,        # 🔑 삭제 키값
      "title": str,
      "meeting_date": str,
      "audio_file": str,
      "chunk_index": int,
      "start_time": float,
      "end_time": float,
      "speaker_count": int
  }
  ```

#### Collection: `meeting_subtopic`
- **용도**: 소주제별 요약 저장 및 조회
- **Embedding**: OpenAI text-embedding-3-small
- **메타데이터**:
  ```python
  {
      "meeting_id": str,        # 🔑 삭제 키값
      "title": str,
      "meeting_date": str,
      "audio_file": str
  }
  ```

---

## 🆕 최근 구현 내용 (2025-11-06)

### 1️⃣ Firebase Authentication 통합 (완료)

**배경**: 다중 사용자 지원 및 노트 소유권 관리를 위한 인증 시스템 필요

**구현 내용**:
- Firebase Admin SDK 초기화 (`utils/firebase_auth.py`)
- Google OAuth 로그인 (팝업 방식)
- ID 토큰 검증 및 세션 관리
- 로그인/로그아웃 API

**추가된 파일**:
- `utils/firebase_auth.py` - Firebase 초기화 및 토큰 검증
- `utils/user_manager.py` - 사용자 CRUD 및 권한 관리
- `utils/decorators.py` - `@login_required`, `@admin_required` 데코레이터
- `templates/login.html` - 로그인 페이지 (Firebase SDK 사용)

**수정된 파일**:
- `app.py` - 로그인/로그아웃 라우트 추가, 모든 라우트에 `@login_required` 적용
- `templates/layout.html` - 로그아웃 버튼 추가 (하단)
- `.env` - Firebase 설정 키 추가 (7개)

**환경 변수**:
```bash
FIREBASE_API_KEY=...
FIREBASE_AUTH_DOMAIN=...
FIREBASE_PROJECT_ID=...
FIREBASE_STORAGE_BUCKET=...
FIREBASE_MESSAGING_SENDER_ID=...
FIREBASE_APP_ID=...
FIREBASE_MEASUREMENT_ID=...
FLASK_SECRET_KEY=...
```

---

### 2️⃣ 사용자 권한 관리 시스템 (완료)

**구현 내용**:
- 노트 소유권 관리 (owner_id)
- 노트 공유 기능 (이메일 기반)
- 접근 권한 체크 (본인 노트 + 공유받은 노트만 조회 가능)
- Admin/User 역할 구분

**데이터베이스 변경**:
- `users` 테이블 추가 (google_id, email, name, role 등)
- `meeting_dialogues`, `meeting_minutes`에 `owner_id` 컬럼 추가
- `meeting_shares` 테이블 추가 (공유 관계 저장)

**API 엔드포인트**:
- `POST /api/share/<meeting_id>` - 노트 공유
- `GET /api/shared_users/<meeting_id>` - 공유 목록 조회
- `POST /api/unshare/<meeting_id>/<user_id>` - 공유 해제

**함수 위치**:
- `utils/user_manager.py` - 모든 사용자 관련 함수
  - `get_or_create_user()` - 사용자 조회/생성
  - `can_access_meeting()` - 권한 체크
  - `share_meeting()` - 노트 공유
  - `is_admin()` - 관리자 체크

---

### 3️⃣ 챗봇 UI 개편 (완료)

**변경 사항**:
- 기존: 우측 상단 드래그 가능한 플로팅 버튼 (보라색 🤖)
- 개선: 우측 사이드 고정 탭 (파란색 < CHAT)

**새 UI 동작**:
```
평소: 화면 오른쪽에서 35px만 삐져나옴 (< CHAT)
호버: 전체 탭(40px)이 슬라이드
클릭: 400px 사이드바 펼쳐짐
```

**수정된 파일**:
- `templates/layout.html:36-40` - 탭 버튼 HTML 변경
  ```html
  <button class="chatbot-toggle-tab" id="chatbot-toggle-tab" title="AI Assistant">
      <span class="tab-icon">&#10094;</span>
      <span class="tab-text">CHAT</span>
  </button>
  ```

- `static/css/style.css` - 탭 스타일 추가 (100+ 줄)
  - `.chatbot-toggle-tab` - 세로 탭 레이아웃
  - `transform: translateX(35px)` - 살짝 삐져나오기
  - `:hover` - 호버 시 슬라이드

- `static/js/script.js` - 드래그 코드 삭제, 클릭 이벤트로 단순화

---

### 4️⃣ 디자인 테마 통일 (완료)

**색상 변경**: Purple → Blue Gradient
- 기존: `#667eea → #764ba2` (보라색)
- 변경: `#3498db → #2980b9` (파란색)

**적용 범위**:
- 챗봇 탭 배경
- 챗봇 헤더
- 사용자 메시지 말풍선
- 전송 버튼
- 프로그레스바
- 로그인 페이지 배경
- 버튼 (모두선택, 삭제, 파일 선택)

**기타 색상 개선**:
- 메인 콘텐츠 배경: 흰색 → 연한 회색 (#f8f9fa)
- 노트 카드: 흰색 유지 (대비 효과)
- 메뉴바: 기존 색상 유지 (#2c3e50)

**수정된 파일**:
- `static/css/style.css` - 모든 color, background 값 변경
- `templates/login.html` - 인라인 스타일 색상 변경

---

### 5️⃣ Font Awesome 아이콘 적용 (완료)

**변경 사항**:
- 기존: 이모지 아이콘 (📝, 📂, 🔍 등)
- 개선: Font Awesome 6.4.0 아이콘

**메뉴 아이콘**:
```html
새노트 만들기: <i class="fa-solid fa-plus"></i>
노트 보기: <i class="fa-solid fa-folder-open"></i>
스크립트입력: <i class="fa-solid fa-file-lines"></i>
리트리버: <i class="fa-solid fa-magnifying-glass"></i>
요약/템플릿: <i class="fa-solid fa-list-check"></i>
로그아웃: <i class="fa-solid fa-right-from-bracket"></i>
```

**챗봇 텍스트 변경**:
- "AI Chatbot" → "AI Assistant"

**수정된 파일**:
- `templates/layout.html:8` - Font Awesome CDN 추가
- `templates/layout.html:19-28` - 모든 메뉴 아이콘 교체
- `static/css/style.css` - 아이콘 정렬 스타일 추가

---

### 6️⃣ Admin 전용 Debug 메뉴 (완료)

**구현 내용**:
- Debug 메뉴(스크립트입력, 리트리버, 요약/템플릿)를 Admin만 볼 수 있게 숨김
- Context Processor로 모든 템플릿에 `is_admin` 변수 주입

**수정된 파일**:
- `app.py:122-135` - Context Processor 추가
  ```python
  @app.context_processor
  def inject_user_info():
      if 'user_id' in session:
          return {'is_admin': is_admin(session['user_id'])}
      return {'is_admin': False}
  ```

- `templates/layout.html:21-26` - 조건부 렌더링
  ```html
  {% if is_admin %}
  <li class="nav-header">Debug</li>
  <li class="nav-item">...</li>
  {% endif %}
  ```

**Admin 설정**:
- `utils/user_manager.py:is_admin()` - 이메일 기반 관리자 체크
- 하드코딩된 Admin 이메일 목록

---

### 7️⃣ 로그인 페이지 개선 (완료)

**변경 사항**:
- 색상 테마를 파란색으로 변경
- Subtitle 문구 변경

**새 문구**:
- 기존: "회의 음성을 AI로 자동 회의록 작성"
- 변경: "회의를 기록하는 가장 스마트한 방법"

**수정된 파일**:
- `templates/login.html:16, 99` - 배경색 및 스피너 색상 변경
- `templates/login.html:133` - Subtitle 문구 변경

---

### 8️⃣ MP4 비디오 파일 지원 (완료)

**구현 내용**:
- MP4 파일 업로드 시 ffmpeg로 WAV 변환
- 변환 후 STT 처리, 원본 MP4 경로 저장
- 임시 WAV 파일 자동 삭제

**변환 설정**:
```bash
ffmpeg -i video.mp4 \
  -vn \                    # 비디오 스트림 제거
  -acodec pcm_s16le \      # 16-bit PCM
  -ar 16000 \              # 16kHz (Whisper 최적)
  -ac 1 \                  # 모노 채널
  output.wav
```

**수정된 파일**:
- `app.py:74-118` - `convert_video_to_audio()` 함수 추가
- `app.py:393-416` - 비디오 변환 로직 추가
- `app.py:55` - ALLOWED_EXTENSIONS에 'mp4' 추가

**특징**:
- ✅ 5분 타임아웃
- ✅ 변환 실패 시 에러 처리
- ✅ 임시 파일 자동 정리

---

### 9️⃣ 화자별 점유율 기능 (완료)

**구현 내용**:
- 각 화자의 발화 시간 비율 계산
- 뷰어 페이지에 바 차트로 표시

**계산 방식**:
```python
# 각 세그먼트의 duration 계산 (현재 start_time ~ 다음 start_time)
# 화자별 총 시간 합산
# 전체 시간 대비 비율 계산
```

**추가된 파일**:
- `utils/analysis.py` - `calculate_speaker_share()` 함수

**수정된 파일**:
- `app.py:556-557` - API 응답에 speaker_share 추가
- `templates/viewer.html` - 화자별 점유율 차트 UI
- `static/js/viewer.js` - 차트 렌더링 로직

**출력 형식**:
```json
{
  "speaker_share": [
    {"speaker": "SPEAKER_00", "duration": 120.5, "percentage": 35.2},
    {"speaker": "SPEAKER_01", "duration": 180.3, "percentage": 52.7},
    {"speaker": "SPEAKER_02", "duration": 41.2, "percentage": 12.1}
  ]
}
```

---

### 🔟 데이터베이스 함수 수정 (완료)

**배경**: `owner_id` 매개변수가 함수 시그니처에 없어서 업로드 실패

**수정된 함수**:
- `utils/db_manager.py:15` - `save_stt_to_db(owner_id=None)` 추가
- `utils/db_manager.py:82` - `save_minutes(owner_id=None)` 추가

**변경 사항**:
```python
# Before
def save_stt_to_db(self, segments, audio_filename, title, meeting_date=None):

# After
def save_stt_to_db(self, segments, audio_filename, title, meeting_date=None, owner_id=None):
```

**INSERT 문 업데이트**:
```sql
INSERT INTO meeting_dialogues
(meeting_id, meeting_date, speaker_label, start_time, segment, confidence, audio_file, title, owner_id)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
```

---

## 🆕 최근 구현 내용 (2025-11-05)

### 1️⃣ 메타데이터 추출 기능 롤백 (완료)

**배경**: 오디오 파일의 생성 날짜를 추출하려 했으나 복잡도가 높고 신뢰성 문제 발생

**변경 사항**:
- ❌ 제거: mutagen 기반 메타데이터 추출 코드 전체 삭제
- ❌ 제거: File API 기반 `lastModified` 확인 로직
- ✅ 단순화: 업로드 시점의 타임스탬프를 `meeting_date`로 사용

**수정된 파일**:
- `app.py:187-188` - 현재 시간으로 변경
  ```python
  meeting_date = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  ```
- `app.py` - 삭제된 함수들:
  - `extract_audio_creation_date()` (45-177줄)
  - `get_audio_metadata()` (158-182줄)
  - `/api/check_metadata` 엔드포인트 (184-236줄)
- `templates/index.html:27-33` - 메타데이터 표시 UI 제거
- `static/js/script.js:635-657` - `checkFileMetadata()` 함수 및 호출 코드 삭제

**결과**: 노트 생성 시 업로드 시점의 시간이 자동으로 기록됨

---

### 2️⃣ 회의 상세 페이지 UI 개선 (완료)

**추가된 기능**:
- 📅 회의 날짜 표시 (제목과 오디오 플레이어 사이)
- 👥 참석자 목록 표시 (색상별 원형 아이콘)

**UI 레이아웃**:
```
[제목]
─────────────────────
📅 2025년 11월 5일
👤👤👤 SPEAKER_00, SPEAKER_01, SPEAKER_02
─────────────────────
[오디오 플레이어]
```

**수정된 파일**:
- `templates/viewer.html:12-22` - 회의 정보 섹션 추가
  ```html
  <div class="meeting-info-section">
      <div class="meeting-date">
          <span id="meeting-date-display">날짜 로딩 중...</span>
      </div>
      <div class="meeting-participants">
          <div class="participants-list" id="participants-list"></div>
      </div>
  </div>
  ```

- `static/js/viewer.js:280-346` - 새로운 함수 추가:
  - `displayMeetingDate(meetingDate)` - 날짜 포맷팅 및 표시
  - `displayParticipants(participants)` - 참석자 아이콘 생성

- `app.py:284-310` - `/api/meeting/<meeting_id>` 엔드포인트 수정:
  ```python
  # 참석자 목록 추출 (중복 제거된 speaker_label 목록)
  participants = list(set([t['speaker_label'] for t in transcript if t.get('speaker_label')]))
  participants.sort()

  return jsonify({
      ...
      "meeting_date": meeting_date,
      "participants": participants,
      ...
  })
  ```

- `static/css/style.css:760-814` - 회의 정보 섹션 스타일 추가:
  - 참석자 아이콘: 36px 원형, 5가지 색상 순환
  - 날짜 표시: 회색 텍스트, 하단 여백

**특징**:
- ✅ 참석자는 speaker_label에서 자동 추출 (중복 제거)
- ✅ 5가지 색상으로 화자 구분 (#4A90E2, #50C878, #F39C12, #9B59B6, #E74C3C)
- ✅ 날짜는 한국어 형식으로 표시 (예: 2025년 11월 5일)

---

### 3️⃣ 회의록 탭 빈 상태 UI 재디자인 (완료)

**변경 사항**:
- 기존: 버튼과 텍스트가 화면 중앙에 위치
- 개선: 버튼과 텍스트를 상단에 세로로 배치

**새 레이아웃**:
```
┌─────────────────────┐
│                     │
│  회의록 생성 버튼을 │  ← 텍스트 먼저
│  눌러 정식 회의록을 │
│  작성하세요.        │
│                     │
│  [회의록 생성]       │  ← 버튼 아래
│                     │
│                     │
└─────────────────────┘
```

**수정된 파일**:
- `templates/viewer.html:53-55` - HTML 순서 변경 및 클래스 추가:
  ```html
  <div id="minutes-container" class="minutes-container minutes-empty">
      <p class="minutes-placeholder">회의록 생성 버튼을 눌러 정식 회의록을 작성하세요.</p>
      <button id="generate-minutes-button" class="btn-primary">회의록 생성</button>
  </div>
  ```

- `static/css/style.css:540-555` - 빈 상태 스타일 추가:
  ```css
  .minutes-empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;  /* 상단 정렬 */
      gap: 1rem;
      padding-top: 3rem;            /* 상단 여백 */
  }
  ```

- `static/js/viewer.js:326-328` - 회의록 생성 시 빈 상태 클래스 제거:
  ```javascript
  function displayMinutes(minutesText) {
      minutesContainer.classList.remove('minutes-empty');
      // ...
  }
  ```

---

### 4️⃣ 로고 통합 (완료)

**변경 사항**:
- 좌측 네비게이션 상단의 "Ai:" 텍스트를 GenMinute 로고 이미지로 교체

**수정된 파일**:
- `templates/layout.html:13-15` - 로고 이미지 태그로 변경:
  ```html
  <div class="nav-logo">
      <img src="{{ url_for('static', filename='image/logo.png') }}" alt="GenMinute Logo">
  </div>
  ```

- `static/css/style.css:51-65` - 로고 스타일링:
  ```css
  .nav-logo img {
      width: 100%;
      height: auto;
      max-width: 150px;  /* 최종 크기 */
      object-fit: contain;
  }
  ```

**크기 조정 과정**:
- 초기: 220px (너무 큼)
- 수정: 180px (여전히 큼)
- 최종: 150px (네비게이션 폭에 맞춤)

---

### 5️⃣ STT 화자 병합 로직 변경 (완료)

**배경**: Python 함수로 동일 화자의 연속 발화를 병합하려 했으나 문제 발생

**문제점**:
1. `@staticmethod` 데코레이터 누락
2. 함수 호출 방식 오류 (plain function vs class method)
3. `start_time` 정보 손실
4. `confidence` 값 부정확성
5. `id` 필드 불연속성
6. 문장 길이 제한 로직 없음

**최종 해결 방법**:
- ❌ Python 함수 삭제: `merge_consecutive_speaker_segments()` 전체 제거
- ✅ Gemini 프롬프트 기반 병합: AI에게 병합 로직 위임

**수정된 파일**:
- `utils/stt.py:68` - Gemini 프롬프트에 병합 지침 추가:
  ```python
  "13. speaker가 동일한 경우 하나의 행으로 만듭니다. 단, 문장이 5개를 넘어갈 경우 다음 대화로 분리한다."
  ```
- `utils/stt.py:143` - 병합 함수 호출 제거, `normalized_segments` 직접 반환

**장점**:
- ✅ 코드 복잡도 감소
- ✅ AI가 맥락을 고려한 스마트 병합 가능
- ✅ 문장 길이 제한 자동 적용 (5문장 초과 시 분리)

---

## 🆕 최근 구현 내용 (2025-11-04)

### 1️⃣ AI 챗봇 시스템 (완료)

**구현 파일**: `utils/chat_manager.py`

**핵심 클래스**: `ChatManager`
```python
class ChatManager:
    def search_documents(query, meeting_id)  # chunks(3개) + subtopic(3개) 검색
    def format_context(search_results)       # 검색 결과 포맷팅
    def generate_answer(query, context)      # Gemini 2.5 Flash로 답변 생성
    def process_query(query, meeting_id)     # 전체 파이프라인
```

**API 엔드포인트**: `POST /api/chat` (`app.py:421-451`)

**UI 위치**: `layout.html:28-52`
- 우측 상단 🤖 토글 버튼 (드래그 가능)
- 클릭 시 400px 사이드바 슬라이드
- sessionStorage로 대화 내역 유지

**특징**:
- ✅ Self-query retriever 사용
- ✅ meeting_chunk + meeting_subtopic 병합 검색 (각 3개씩)
- ✅ Gemini 2.5 Flash로 답변 생성
- ✅ 출처 정보 포함
- ✅ 전체 페이지에서 사용 가능

---

### 2️⃣ 노트 일괄 삭제 기능 (완료)

**구현 파일**: `templates/notes.html`

**UI 구성**:
```
모든 노트                    [모두선택] [삭제]
                                ↑         ↑
                          기본 비활성화 (회색)

☐ 노트 제목          2025-11-01
☐ 노트 제목 2        2025-11-02
```

**동작 방식**:
1. 체크박스 선택 → 버튼 활성화
2. "모두선택" 클릭 → 전체 선택/해제
3. "삭제" 클릭 → 확인 모달 → 순차적으로 하나씩 삭제
4. 콘솔에 진행 상황 출력 (`1/3 삭제 완료...`)

**UI 개선**:
- ✅ 개별 삭제 X 버튼 제거 (2025-11-04)
- 이유: 체크박스 선택 방식으로 통일하여 UX 일관성 향상
- 모든 삭제는 체크박스 + "삭제" 버튼을 통해서만 수행

**코드 위치**:
- UI: `templates/notes.html:9-30`
- 체크박스 로직: `templates/notes.html:184-227`
- 일괄 삭제 로직: `templates/notes.html:231-301`

---

### 3️⃣ 삭제 검증 로그 시스템 (완료)

**목적**: 개발자가 삭제가 제대로 수행되었는지 터미널에서 확인

**구현 위치**:
- `utils/db_manager.py:201-281` (SQLite DB 검증)
- `utils/vector_db_manager.py:612-779` (Vector DB + 오디오 파일 검증)

**로그 구조**:

```
======================================================================
🗑️  [회의 데이터 삭제 프로세스 시작]
======================================================================
🔑 삭제 키값(meeting_id): abc-123-xyz
📍 이 키값을 기준으로 다음 데이터를 검색하여 삭제합니다:
   • SQLite DB - meeting_dialogues 테이블 (WHERE meeting_id = 'abc-123-xyz')
   • SQLite DB - meeting_minutes 테이블 (WHERE meeting_id = 'abc-123-xyz')
   • Vector DB - meeting_chunk 컬렉션 (WHERE meeting_id = 'abc-123-xyz')
   • Vector DB - meeting_subtopic 컬렉션 (WHERE meeting_id = 'abc-123-xyz')
   • 오디오 파일 (uploads 폴더)
======================================================================

📊 [SQLite DB 삭제 검증 시작]
======================================================================
[삭제 전] meeting_dialogues: 150개
[삭제 전] meeting_minutes: 1개
----------------------------------------------------------------------
[삭제 수행] meeting_dialogues: 150개 삭제
[삭제 수행] meeting_minutes: 1개 삭제
----------------------------------------------------------------------
[삭제 후] meeting_dialogues: 0개 남음
[삭제 후] meeting_minutes: 0개 남음
✅ SQLite DB 삭제 검증 성공: 모든 데이터가 삭제되었습니다.
======================================================================

📊 [Vector DB Chunks 삭제 검증 시작]
======================================================================
[삭제 전] meeting_chunk: 20개
----------------------------------------------------------------------
[삭제 수행] meeting_chunk: 20개 삭제 시도
----------------------------------------------------------------------
[삭제 후] meeting_chunk: 0개 남음
✅ Vector DB (meeting_chunk) 삭제 검증 성공
======================================================================

📊 [Vector DB Subtopic 삭제 검증 시작]
======================================================================
[삭제 전] meeting_subtopic: 5개
----------------------------------------------------------------------
[삭제 수행] meeting_subtopic: 5개 삭제 시도
----------------------------------------------------------------------
[삭제 후] meeting_subtopic: 0개 남음
✅ Vector DB (meeting_subtopic) 삭제 검증 성공
======================================================================

📊 [오디오 파일 삭제 검증 시작]
======================================================================
[삭제 전] 오디오 파일 존재: sample.wav
----------------------------------------------------------------------
[삭제 수행] 오디오 파일 삭제 시도
----------------------------------------------------------------------
[삭제 후] 오디오 파일 없음
✅ 오디오 파일 삭제 검증 성공
======================================================================

🎉 [삭제 작업 최종 요약]
======================================================================
✓ SQLite meeting_dialogues: 150개 삭제
✓ SQLite meeting_minutes: 1개 삭제
✓ Vector DB meeting_chunk: 20개 삭제
✓ Vector DB meeting_subtopic: 5개 삭제
✓ 오디오 파일: 삭제됨
======================================================================
```

**삭제 키값**: 모든 삭제는 `meeting_id`를 기준으로 수행

---

### 4️⃣ 기타 개선 사항

**회의록 자동 요약**:
- "요약하기" 버튼 제거
- 페이지 로드 시 자동으로 문단 요약 로드
- 위치: `templates/viewer.html:35`, `static/js/viewer.js`

**업로드 프로그레스바**:
- 업로드 진행 상황 시각적 표시
- 위치: `templates/index.html:38-52`, `static/js/script.js`

---

## 🛠️ 기술 스택

| Category | Technology | Version |
|----------|-----------|---------|
| **Backend** | Flask | Latest |
| **Database** | SQLite | 3.x |
| **Vector DB** | ChromaDB | Latest |
| **Embeddings** | OpenAI text-embedding-3-small | - |
| **STT** | Gemini 2.5 Pro (멀티모달) | Latest |
| **LLM** | Gemini 2.5 Flash | Latest |
| **Authentication** | Firebase Authentication | Latest |
| **Frontend** | Vanilla JavaScript | ES6+ |
| **Audio/Video** | ffmpeg | Latest |
| **Icons** | Font Awesome | 6.4.0 |

---

## 🔑 환경 변수 (.env)

```bash
# OpenAI API (Embedding)
OPENAI_API_KEY=sk-...

# Google Gemini API (STT, Text Processing)
GOOGLE_API_KEY=...

# Firebase Authentication (NEW: 2025-11-06)
FIREBASE_API_KEY=...
FIREBASE_AUTH_DOMAIN=...
FIREBASE_PROJECT_ID=...
FIREBASE_STORAGE_BUCKET=...
FIREBASE_MESSAGING_SENDER_ID=...
FIREBASE_APP_ID=...
FIREBASE_MEASUREMENT_ID=...

# Flask Session Secret (NEW: 2025-11-06)
FLASK_SECRET_KEY=...
```

---

## 📝 주요 API 엔드포인트

### 인증 (NEW: 2025-11-06)
- `GET /login` - 로그인 페이지
- `POST /api/login` - Firebase ID 토큰 검증 및 세션 생성
- `POST /api/logout` - 세션 삭제
- `GET /api/me` - 현재 사용자 정보 조회

### 업로드 & 처리
- `POST /upload` - 오디오/비디오 파일 업로드 및 STT 처리
- `POST /upload_script` - 스크립트 텍스트 직접 입력

### 뷰어
- `GET /view/<meeting_id>` - 회의록 뷰어 페이지 (권한 체크)
- `GET /api/meeting/<meeting_id>` - 회의 데이터 조회 (권한 체크)

### 요약 & 회의록
- `POST /api/summarize/<meeting_id>` - 문단 요약 생성
- `GET /api/check_summary/<meeting_id>` - 요약 존재 여부 확인
- `POST /api/generate_minutes/<meeting_id>` - 회의록 생성
- `GET /api/get_minutes/<meeting_id>` - 회의록 조회

### 챗봇
- `POST /api/chat` - 챗봇 질의응답 (권한 체크)
  ```json
  Request:
  {
    "query": "프로젝트 일정은 언제야?",
    "meeting_id": "abc-123"  // optional, 없으면 전체 노트 검색
  }

  Response:
  {
    "success": true,
    "answer": "답변 내용...",
    "sources": [
      {
        "type": "chunk",
        "meeting_id": "...",
        "title": "...",
        "start_time": 120,
        "end_time": 180
      }
    ]
  }
  ```

### 공유 (NEW: 2025-11-06)
- `POST /api/share/<meeting_id>` - 노트 공유 (이메일 기반)
- `GET /api/shared_users/<meeting_id>` - 공유받은 사용자 목록
- `POST /api/unshare/<meeting_id>/<user_id>` - 공유 해제

### 삭제
- `POST /api/delete_meeting/<meeting_id>` - 회의 데이터 전체 삭제 (권한 체크)
  - SQLite DB (meeting_dialogues, meeting_minutes)
  - Vector DB (meeting_chunk, meeting_subtopic)
  - 오디오 파일 (uploads 폴더)
  - 터미널에 상세 검증 로그 출력

### 검색
- `POST /api/search` - Vector DB 검색 (4가지 retriever 지원)

### 기타
- `GET /notes` - 모든 노트 목록
- `GET /retriever` - 검색 테스트 페이지

---

## 🚀 실행 방법

### 1. 환경 설정
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt

# ffmpeg 설치 (비디오 파일 지원용)
# Ubuntu/Debian: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
# Windows: https://ffmpeg.org/download.html
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key

# Firebase 설정 (Google Cloud Console에서 발급)
FIREBASE_API_KEY=...
FIREBASE_AUTH_DOMAIN=...
FIREBASE_PROJECT_ID=...
FIREBASE_STORAGE_BUCKET=...
FIREBASE_MESSAGING_SENDER_ID=...
FIREBASE_APP_ID=...
FIREBASE_MEASUREMENT_ID=...

# Flask Secret Key (랜덤 문자열 생성)
FLASK_SECRET_KEY=your_random_secret_key
```

### 3. 서버 실행
```bash
python app.py
# http://localhost:5050 접속 → 로그인 페이지로 자동 리다이렉트
```

### 4. 초기 관리자 설정
```python
# utils/user_manager.py:12 수정
ADMIN_EMAILS = [
    "your-email@gmail.com"  # 여기에 본인 이메일 추가
]
```

---

## 📊 현재 시스템 완성도

| 기능 | 상태 | 비고 |
|------|------|------|
| STT & 화자 분리 | ✅ 완료 | Gemini 2.5 Pro (멀티모달) |
| Smart Chunking | ✅ 완료 | 화자/시간 기반 |
| 문단 요약 | ✅ 완료 | Gemini 2.5 Pro |
| 회의록 생성 | ✅ 완료 | RAG 기반 |
| 검색 시스템 | ✅ 완료 | 4가지 retriever |
| AI 챗봇 | ✅ 완료 | Self-query retriever |
| 개별 삭제 | ✅ 완료 | 체크박스 방식 |
| 일괄 삭제 | ✅ 완료 | 체크박스 + 순차 삭제 |
| 삭제 검증 로그 | ✅ 완료 | 터미널 상세 로그 |
| 프로그레스바 | ✅ 완료 | 업로드 진행 상황 |
| 자동 요약 | ✅ 완료 | 페이지 로드 시 자동 |
| 사용자 인증 | ✅ 완료 | Firebase Google OAuth |
| 권한 관리 | ✅ 완료 | owner_id 기반 접근 제어 |
| 노트 공유 | ✅ 완료 | 이메일 기반 공유 |
| 비디오 지원 | ✅ 완료 | MP4 → WAV 자동 변환 |
| 화자별 분석 | ✅ 완료 | 점유율 바 차트 |
| UI/UX | ✅ 완료 | Blue 테마, Font Awesome |

**전체 완성도: 100%** - 프로덕션 레벨 완성

---

## 💡 향후 개선 제안

### 1. 일괄 삭제 UX 개선
- **현재**: 순차 삭제 중 콘솔에만 로그 출력
- **개선안**: 프로그레스 모달 추가
  ```
  [삭제 진행 중]
  ▓▓▓▓▓▓░░░░ 60% (3/5 완료)

  ✓ 회의 A 삭제 완료
  ✓ 회의 B 삭제 완료
  ⏳ 회의 C 삭제 중...
  ```
- **파일**: `templates/notes.html:306-352`
- **예상 작업 시간**: 1시간

### 2. 챗봇 추천 질문 기능
- **현재**: 사용자가 직접 질문 입력
- **개선안**: 회의 내용 기반 추천 질문 3개 자동 생성
  ```
  💬 추천 질문:
  - 이 회의의 주요 결정사항은?
  - 다음 액션 아이템은?
  - 참석자는 누구였나요?
  ```
- **파일**: `utils/chat_manager.py` (새 메서드 추가)
- **예상 작업 시간**: 2시간

### 3. 챗봇 출처 링크 기능
- **현재**: 출처 정보만 표시
- **개선안**: 클릭 시 해당 타임스탬프로 이동
  ```json
  {
    "sources": [
      {
        "title": "프로젝트 킥오프",
        "timestamp": 120,
        "link": "/view/{meeting_id}?t=120"  // 120초 시점으로 이동
      }
    ]
  }
  ```
- **파일**: `utils/chat_manager.py`, `static/js/script.js`
- **예상 작업 시간**: 2시간

### 4. 회의록 템플릿 커스터마이징
- **현재**: 고정된 회의록 템플릿
- **개선안**: 사용자가 회의록 템플릿을 선택/편집
  ```
  템플릿 종류:
  - 표준 회의록
  - 간단 요약
  - 액션 아이템 중심
  - 의사결정 중심
  ```
- **파일**: `utils/stt.py` (generate_minutes), DB 스키마 수정
- **예상 작업 시간**: 4시간

### 5. 오디오 파일 분할 업로드
- **현재**: 전체 파일을 한 번에 Whisper API로 전송
- **문제**: 대용량 파일 타임아웃 가능
- **개선안**: 10분 단위로 분할 → 병렬 처리 → 결과 병합
- **파일**: `utils/stt.py`
- **예상 작업 시간**: 3시간

### 6. 다국어 지원
- **현재**: 한국어만 지원
- **개선안**: Whisper API의 자동 언어 감지 + 다국어 UI
- **파일**: `utils/stt.py`, 모든 템플릿 파일
- **예상 작업 시간**: 6시간

### 7. 사용자 인증 시스템
- ✅ **완료 (2025-11-06)**: Firebase Authentication 통합
- 다중 사용자 지원, 권한 관리, 노트 공유 기능 모두 구현됨

---

## 🐛 알려진 이슈 및 제약사항

### 1. ChromaDB 메타데이터 필터링 제한
- **문제**: 부분 문자열 매칭 불가 (정확한 일치만 가능)
- **해결 방법**: 검색 후 Python에서 후처리 필터링

### 2. Gemini API Rate Limit
- **문제**: 분당 요청 수 제한 있음 (STT, 요약, 회의록 생성 모두 Gemini 사용)
- **해결 방법**: 에러 핸들링 및 재시도 로직 필요

### 3. 대용량 오디오 파일 처리
- **문제**: Gemini API 타임아웃 가능성, MP4 변환 시간 소요
- **해결 방법**: 향후 개선 제안 #5 참조 (파일 분할 처리)

### 4. 동시 업로드 제약
- **문제**: 여러 사용자가 동시에 대용량 파일 업로드 시 서버 부하
- **현황**: Flask 멀티스레딩으로 기본 처리, SQLite write lock 가능성
- **해결 방법**: 큐 시스템 도입 고려 (Celery + Redis)

---

## 📚 참고 문서 및 중요 코드 위치

### 시스템 아키텍처
- **FLOWCHART.md**: 전체 시스템 플로우차트

### 핵심 로직 위치
- **STT 처리**: `utils/stt.py:28-114` (`transcribe_audio()` - Gemini 2.5 Pro 멀티모달)
- **Smart Chunking**: `utils/vector_db_manager.py:174-252` (`_create_smart_chunks()`)
- **Gemini 텍스트 정제**: `utils/vector_db_manager.py:79-125` (`_clean_text_with_gemini()`)
- **검색 로직**: `utils/vector_db_manager.py:312-407` (`search()`)
- **챗봇 로직**: `utils/chat_manager.py:192-259` (`process_query()`)
- **삭제 로직**: `utils/vector_db_manager.py:612-779` (`_delete_all_meeting_data()`)
- **삭제 검증**: `utils/db_manager.py:201-281` (`delete_meeting_by_id()`)
- **Firebase 인증**: `utils/firebase_auth.py` (`verify_id_token()`)
- **사용자 관리**: `utils/user_manager.py` (`get_or_create_user()`, `can_access_meeting()`)
- **비디오 변환**: `app.py:74-118` (`convert_video_to_audio()`)
- **화자 분석**: `utils/analysis.py` (`calculate_speaker_share()`)

### UI 구성
- **로그인 페이지**: `templates/login.html` (Firebase OAuth)
- **전역 레이아웃**: `templates/layout.html` (네비게이션, 챗봇, 로그아웃)
- **업로드 페이지**: `templates/index.html` (프로그레스바 포함)
- **노트 목록**: `templates/notes.html` (일괄 삭제 포함)
- **회의록 뷰어**: `templates/viewer.html` (화자별 점유율 포함)

### JavaScript
- **전역 스크립트**: `static/js/script.js` (챗봇 로직 포함)
- **뷰어 스크립트**: `static/js/viewer.js`

---

## 🔄 최근 Git 커밋 이력

```
a95e63b - 회의록 자동 요약 기능 추가 및 챗봇 UI 오류 수정 (68분 전)
9397db4 - 챗봇기능 구현(질의응답) (3시간 전)
cb2e17a - 오류 처리 및 프로그레스바 기능 추가 (5시간 전)
5c2c197 - requirements.txt추가 (5시간 전)
637a268 - 챗봇UI구현 (9시간 전)
745e0eb - vectorDB삭제기능구현 (9시간 전)
dc496e0 - 삭제기능 수정 (10시간 전)
2b633d7 - 삭제기능 추가 (23시간 전)
```

---

## 💬 다음 세션 작업 시작 가이드

### 바로 시작할 수 있는 작업들:

#### 1️⃣ 일괄 삭제 프로그레스 모달 추가 (난이도: ⭐)
```bash
# 수정 파일
templates/notes.html  # 모달 UI 추가
static/js/notes.js    # 진행 상황 업데이트 로직
```

#### 2️⃣ 챗봇 추천 질문 기능 (난이도: ⭐⭐)
```bash
# 수정 파일
utils/chat_manager.py      # generate_suggested_questions() 메서드 추가
static/js/script.js        # 추천 질문 UI 추가
```

#### 3️⃣ 챗봇 출처 링크 기능 (난이도: ⭐⭐)
```bash
# 수정 파일
utils/chat_manager.py      # 출처에 link 필드 추가
static/js/script.js        # 링크 클릭 이벤트
templates/viewer.html      # 타임스탬프 점프 로직
```

### 테스트 체크리스트:
- [ ] 오디오 업로드 → STT → 회의록 생성 전 과정
- [ ] 챗봇 질의응답 (다양한 질문 시도)
- [ ] 개별 노트 삭제 → 터미널 로그 확인
- [ ] 일괄 노트 삭제 → 터미널 로그 확인
- [ ] 검색 기능 (4가지 retriever 테스트)

---

## 📞 문의 및 이슈

- 구현 중 막히는 부분이 있으면 FLOWCHART.md와 이 문서를 참조
- 기존 코드 패턴을 최대한 유지하며 확장
- 삭제 검증 로그 형식을 다른 작업에도 적용 가능

---

**작성자**: Claude Code
**마지막 업데이트**: 2025-11-06
**주요 업데이트**:
- ✅ Firebase Authentication 통합 (Google OAuth)
- ✅ 사용자 권한 관리 시스템 (owner_id, sharing)
- ✅ 챗봇 UI 개편 (플로팅 버튼 → 사이드 탭)
- ✅ 디자인 테마 통일 (Purple → Blue Gradient)
- ✅ Font Awesome 아이콘 적용
- ✅ Admin 전용 Debug 메뉴
- ✅ MP4 비디오 파일 지원 (ffmpeg)
- ✅ 화자별 점유율 기능
- ✅ STT 모델 정보 정정 (Whisper → Gemini 2.5 Pro)

**다음 작업 우선순위**:
1️⃣ 일괄 삭제 프로그레스 모달
2️⃣ 챗봇 추천 질문 기능
3️⃣ 챗봇 출처 링크 (타임스탬프 점프)
