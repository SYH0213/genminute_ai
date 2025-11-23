# 01. Minute AI 프로젝트 개요 (5분 읽기)

> **레벨 1**: 처음 프로젝트를 접하는 사람을 위한 빠른 이해 가이드

---

## 🎯 프로젝트 한 줄 요약

**회의 음성/영상을 업로드하면 AI가 자동으로 전사, 요약, 회의록을 생성하고 챗봇으로 질의응답까지 제공하는 웹 서비스**

---

## 📌 핵심 기능 3줄 요약

1. **STT (Speech-to-Text)**: 음성/영상 파일 → Gemini 2.5 Pro로 화자 분리 + 전사
2. **AI 요약 & 회의록**: 전사 내용 → Gemini가 문단 요약 + 정식 회의록 + 마인드맵 생성
3. **RAG 챗봇**: ChromaDB 벡터 검색 + Gemini 2.5 Flash로 회의 내용 기반 Q&A

---

## 🛠️ 기술 스택

### Backend
```
Flask 3.1.2                    # 웹 프레임워크
├── Google Gemini 2.5 Pro      # STT, 요약, 회의록 생성
├── Google Gemini 2.5 Flash    # 챗봇, 마인드맵
├── ChromaDB                   # 벡터 데이터베이스
├── OpenAI Embeddings          # text-embedding-ada-002
├── SQLite                     # 관계형 데이터베이스
├── Firebase Authentication    # Google OAuth 로그인
└── ffmpeg                     # 비디오 → 오디오 변환
```

### Frontend
```
Jinja2 템플릿
├── Vanilla JavaScript
├── Chart.js (화자 비중 시각화)
└── Markmap (마인드맵 렌더링)
```

---

## 📊 시스템 플로우 다이어그램

```
[사용자 업로드]
    ↓
┌─────────────────────────────────────┐
│  1. 파일 업로드 & 검증              │
│     - WAV, MP3, M4A, FLAC, MP4      │
│     - 최대 500MB                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  2. 비디오 변환 (MP4인 경우)        │
│     - ffmpeg로 WAV 추출             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. Gemini STT 처리                 │
│     - 화자 분리 (SPEAKER_00, 01...) │
│     - 타임스탬프 추출               │
│     - 신뢰도 점수 계산              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  4. 데이터베이스 저장               │
│     - SQLite: 전사 세그먼트         │
│     - ChromaDB: 스마트 청킹 + 임베딩│
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  5. AI 요약 생성                    │
│     - Gemini로 주제별 요약          │
│     - ChromaDB에 저장               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  6. 마인드맵 생성                   │
│     - Gemini로 키워드 추출          │
│     - SQLite에 저장                 │
└─────────────────────────────────────┘
    ↓
[회의록 뷰어 페이지로 이동]
    ↓
[사용자가 챗봇으로 질문]
    ↓
┌─────────────────────────────────────┐
│  7. RAG 챗봇 응답                   │
│     - ChromaDB 벡터 검색 (상위 6개) │
│     - Gemini Flash로 답변 생성      │
│     - 출처 정보 반환                │
└─────────────────────────────────────┘
```

---

## 📁 프로젝트 구조 (간단 버전)

```
genminute_ai/
├── app.py                    # Flask 앱 진입점
├── config.py                 # 환경 변수 관리
├── init_db.py                # DB 초기화 스크립트
│
├── routes/                   # HTTP 라우트 (Blueprint)
│   ├── auth.py              # 로그인, 로그아웃
│   ├── meetings.py          # 회의 CRUD, 업로드
│   ├── summary.py           # 요약, 회의록 생성
│   ├── chat.py              # 챗봇 Q&A
│   └── admin.py             # Admin 전용 기능
│
├── services/                 # 비즈니스 로직
│   └── upload_service.py    # 파일 업로드 처리
│
├── utils/                    # 인프라 & 유틸리티
│   ├── stt.py               # Gemini STT
│   ├── db_manager.py        # SQLite 관리
│   ├── vector_db_manager.py # ChromaDB 관리
│   ├── chat_manager.py      # 챗봇 로직
│   ├── firebase_auth.py     # Firebase 인증
│   ├── user_manager.py      # 사용자 권한 관리
│   ├── decorators.py        # @login_required 등
│   ├── validation.py        # 입력 검증
│   └── analysis.py          # 화자 비중 분석
│
├── templates/                # Jinja2 HTML
├── static/                   # CSS, JS
├── database/                 # SQLite + ChromaDB
└── uploads/                  # 업로드된 파일
```

---

## 🔑 핵심 개념 이해

### 1. **싱글톤 패턴**
주요 매니저 클래스들은 싱글톤으로 구현되어 있습니다:
- `DatabaseManager`
- `VectorDBManager`
- `STTManager`
- `ChatManager`

→ 앱 실행 중 단 하나의 인스턴스만 존재하여 리소스 효율화

### 2. **스마트 청킹 (Smart Chunking)**
회의 전사본을 단순히 1000자씩 자르는 게 아니라:
- 화자 변경 감지
- 시간 간격 (60초 이상 공백 = 주제 전환)
- 의미적 일관성 유지

→ RAG 검색 정확도 향상

### 3. **RAG (Retrieval-Augmented Generation)**
```
사용자 질문
    ↓
ChromaDB에서 관련 문서 6개 검색 (chunks 3개 + subtopic 3개)
    ↓
검색된 문서를 컨텍스트로 Gemini에게 전달
    ↓
Gemini가 컨텍스트 기반으로만 답변 생성
```

→ 환각(hallucination) 방지, 신뢰성 있는 답변

### 4. **권한 관리 3단계**
1. **Owner**: 본인이 생성한 노트 (수정 가능)
2. **Shared User**: 공유받은 노트 (읽기만 가능)
3. **Admin**: 모든 노트 접근 가능

---

## 🚀 빠른 시작 (로컬 실행)

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경 변수 설정 (.env 파일 생성)
FLASK_SECRET_KEY=<랜덤키>
GOOGLE_API_KEY=<Gemini API 키>
OPENAI_API_KEY=<OpenAI API 키>
FIREBASE_API_KEY=<Firebase 설정>
# ... (나머지 Firebase 설정)

# 4. DB 초기화
python init_db.py

# 5. 서버 실행
python app.py
# → http://localhost:5050
```

---

## 📈 주요 메트릭

| 항목 | 수치 |
|------|------|
| **지원 파일 형식** | WAV, MP3, M4A, FLAC, MP4 |
| **최대 파일 크기** | 500MB |
| **STT 모델** | Gemini 2.5 Pro |
| **챗봇 응답 속도** | 평균 3.77초 |
| **챗봇 성공률** | 100% (테스트 20개 질문 기준) |
| **Vector 검색 개수** | chunks 3개 + subtopic 3개 |

---

## 🎓 학습 경로 추천

1. **입문자**: 이 문서 → `02_architecture.md`
2. **개발자**: `02_architecture.md` → 관심 기능별 레벨3 문서
3. **리뷰어**: `12_code_review_checklist.md` → 레벨4 상세 분석
4. **API 사용자**: `11_api_specification.md`

---

## 📞 다음 단계

- **전체 구조 파악**: `02_architecture.md`로 이동
- **기능별 상세 이해**: `03~07` 번 문서 선택
- **코드 수준 분석**: `08~10` 번 문서 참고
