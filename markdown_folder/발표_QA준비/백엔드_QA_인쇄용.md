# 백엔드 완벽 가이드 - Q&A 인쇄용
## Minute AI 시스템 질의응답

> 백엔드 & 데이터베이스 100문 100답
> 작성일: 2025-11-11

---

# 목차

## 1부. 시스템 아키텍처 (Q1-Q10)
## 2부. 데이터베이스 (Q11-Q30)
## 3부. 백엔드 모듈 (Q31-Q50)
## 4부. API 엔드포인트 (Q51-Q65)
## 5부. 실전 프로세스 (Q66-Q80)
## 6부. 최적화 & 보안 (Q81-Q100)

---

# 1부. 시스템 아키텍처

## Q1. 전체 시스템 아키텍처는 어떻게 구성되어 있나요?

**A1.** 4계층 구조로 되어 있습니다:

1. **프레젠테이션 계층**: Flask 웹 애플리케이션 (app.py)
2. **비즈니스 로직 계층**: Utils 모듈들 (stt, db_manager, vector_db, chat_manager)
3. **데이터 계층**: SQLite (메타데이터) + ChromaDB (벡터 검색)
4. **외부 API 계층**: Gemini AI, Firebase Auth, OpenAI

---

## Q2. 사용하는 주요 기술 스택은 무엇인가요?

**A2.** 다음과 같습니다:

| 용도 | 기술 |
|------|------|
| 웹 프레임워크 | Flask 3.0 |
| 관계형 DB | SQLite3 |
| 벡터 DB | ChromaDB + LangChain |
| AI - STT/요약 | Gemini 2.5 Pro/Flash |
| AI - 임베딩 | OpenAI text-embedding-3-small (1536차원) |
| 인증 | Firebase Auth (Google OAuth) |

---

## Q3. 디렉토리 구조는 어떻게 되나요?

**A3.** 다음과 같이 구성되어 있습니다:

```
minute_ai/
├── app.py                    # Flask 메인 애플리케이션
├── utils/                    # 핵심 비즈니스 로직
│   ├── stt.py               # 음성 인식 & AI 생성
│   ├── db_manager.py        # SQLite CRUD
│   ├── vector_db_manager.py # ChromaDB 관리
│   ├── chat_manager.py      # RAG 챗봇
│   └── user_manager.py      # 사용자/권한 관리
├── database/
│   ├── minute_ai.db         # SQLite 파일
│   └── vector_db/           # ChromaDB 데이터
└── uploads/                 # 업로드 파일
```

---

## Q4. Flask 애플리케이션은 어떻게 초기화되나요?

**A4.** app.py의 36-69번 줄에서 초기화됩니다:

```python
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['UPLOAD_FOLDER'] = "./uploads"
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# 전역 객체 초기화
db = DatabaseManager(DB_PATH)
stt_manager = STTManager()
vdb_manager = VectorDBManager()
chat_manager = ChatManager(vdb_manager)
```

---

## Q5. 파일 업로드부터 회의록 생성까지 전체 데이터 흐름은?

**A5.** 다음과 같은 11단계 파이프라인입니다:

1. 파일 업로드 (app.py)
2. 파일 검증 및 저장 (uploads/)
3. MP4 → WAV 변환 (필요시)
4. Gemini STT 실행 → segments
5. SQLite 저장 (meetings, meeting_dialogues)
6. 스마트 청킹 (화자/시간/크기 고려)
7. ChromaDB 저장 (meeting_chunks)
8. 요약 생성 (Gemini Flash)
9. ChromaDB 저장 (meeting_subtopic)
10. 마인드맵 생성 (Gemini Flash)
11. SQLite 저장 (meeting_minutes)

**소요 시간** (30분 회의): 약 4분

---

## Q6. 메인 Flask 라우트는 어떤 것들이 있나요?

**A6.** 다음과 같은 주요 라우트가 있습니다:

**인증**:
- `/login`: 로그인 페이지
- `/api/login`: Firebase 인증 처리
- `/logout`: 로그아웃

**메인 페이지**:
- `/`: 회의록 목록
- `/viewer/<meeting_id>`: 회의록 상세보기
- `/shared-notes`: 공유받은 노트

**파일 처리**:
- `/api/upload`: 파일 업로드 & 전체 파이프라인
- `/api/upload_with_progress`: SSE로 진행률 전송

**CRUD**:
- `/api/meeting/<meeting_id>`: 회의 정보 조회
- `/api/update_title/<meeting_id>`: 제목 수정
- `/api/delete_meeting/<meeting_id>`: 회의 삭제

**챗봇**:
- `/api/chat`: RAG 챗봇 질의

**공유**:
- `/api/share/<meeting_id>`: 회의록 공유

---

## Q7. 외부 API는 어떤 것들을 사용하나요?

**A7.** 3가지 외부 API를 사용합니다:

1. **Gemini AI**:
   - Gemini 2.5 Pro: STT (화자 분리)
   - Gemini 2.5 Flash: 요약, 마인드맵, 챗봇 답변

2. **OpenAI**:
   - text-embedding-3-small: 벡터 임베딩 (1536차원)

3. **Firebase**:
   - Firebase Auth: Google OAuth 인증

---

## Q8. 왜 Gemini Pro와 Flash를 구분해서 사용하나요?

**A8.** 속도와 비용 최적화 때문입니다:

- **Gemini 2.5 Pro**: STT 전용
  - 화자 분리 정확도가 중요
  - 실시간성보다 정확성 우선

- **Gemini 2.5 Flash**: 요약/마인드맵/챗봇
  - Pro 대비 10배 빠름
  - 비용 절감
  - 품질도 충분히 좋음

---

## Q9. 개발 환경과 프로덕션 환경의 차이는?

**A9.** 주요 차이점:

**개발 환경**:
- Flask 내장 서버 (Werkzeug)
- DEBUG = True
- SQLite 로컬 파일

**프로덕션 환경** (GCP):
- Gunicorn WSGI 서버
- DEBUG = False
- 환경 변수로 API 키 관리
- 로깅 강화
- 에러 핸들링 추가

---

## Q10. 시스템의 주요 성능 지표는?

**A10.** 다음과 같습니다:

- **STT 처리 시간**: 30분 회의 → 2-3분
- **청킹 & 임베딩**: 약 30초
- **요약 생성**: 약 30초
- **챗봇 응답 시간**: 평균 3.77초
- **챗봇 성공률**: 100% (테스트 기준)

---

# 2부. 데이터베이스

## Q11. SQLite에는 어떤 테이블이 있나요?

**A11.** 5개의 테이블이 있습니다:

1. **users**: 사용자 정보
2. **meetings**: 회의 메타데이터
3. **meeting_dialogues**: 대화 내용
4. **meeting_minutes**: 회의록 및 마인드맵
5. **meeting_shares**: 공유 관리

---

## Q12. users 테이블의 구조는?

**A12.** 다음과 같습니다:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firebase_uid TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

**역할**: Firebase 사용자와 내부 user_id 매핑

---

## Q13. meetings 테이블의 구조는?

**A13.** 다음과 같습니다:

```sql
CREATE TABLE meetings (
    id TEXT PRIMARY KEY,              -- UUID v4
    title TEXT NOT NULL,
    meeting_date TIMESTAMP NOT NULL,
    audio_file TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
```

**인덱스**:
- `idx_meetings_owner`: 소유자별 조회 최적화
- `idx_meetings_date`: 날짜순 정렬 최적화

---

## Q14. meeting_dialogues 테이블의 구조는?

**A14.** 다음과 같습니다:

```sql
CREATE TABLE meeting_dialogues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL,
    speaker_label TEXT NOT NULL,      -- "화자1", "화자2"
    start_time REAL NOT NULL,         -- 초 단위
    segment TEXT NOT NULL,            -- 대화 내용
    confidence REAL,                  -- 0.0-1.0
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);
```

**역할**: STT 결과 저장 (화자별 타임스탬프 포함)

---

## Q15. meeting_minutes 테이블의 구조는?

**A15.** 다음과 같습니다:

```sql
CREATE TABLE meeting_minutes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    meeting_date TIMESTAMP NOT NULL,
    content TEXT NOT NULL,            -- 마크다운 회의록
    mindmap_content TEXT,             -- 마크다운 마인드맵
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);
```

---

## Q16. meeting_shares 테이블의 구조는?

**A16.** 다음과 같습니다:

```sql
CREATE TABLE meeting_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL,
    shared_with_user_id INTEGER NOT NULL,
    permission TEXT DEFAULT 'read',   -- 'read', 'write', 'admin'
    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(meeting_id, shared_with_user_id)
);
```

**역할**: 회의록 공유 및 권한 관리

---

## Q17. ChromaDB에는 어떤 컬렉션이 있나요?

**A17.** 2개의 컬렉션이 있습니다:

1. **meeting_chunks**: 실제 대화 내용 (청킹된 텍스트)
2. **meeting_subtopic**: 주제별 요약

---

## Q18. meeting_chunks 컬렉션의 Document 구조는?

**A18.** 다음과 같습니다:

```python
{
    "id": "{meeting_id}_chunk_{index}",
    "text": "청크 텍스트 (화자/시간 정보 제거됨)",
    "metadata": {
        "meeting_id": "uuid",
        "dialogue_id": "{meeting_id}_chunk_{index}",
        "chunk_index": 0,
        "title": "회의 제목",
        "meeting_date": "2025-11-10",
        "audio_file": "uuid.mp3",
        "start_time": 120.5,
        "end_time": 180.2,
        "speaker_count": 2
    },
    "embedding": [0.1, 0.2, ...]  # 1536차원
}
```

---

## Q19. meeting_subtopic 컬렉션의 Document 구조는?

**A19.** 다음과 같습니다:

```python
{
    "id": "{meeting_id}_summary_{index}",
    "text": "요약 텍스트 (마크다운)",
    "metadata": {
        "meeting_id": "uuid",
        "meeting_title": "회의 제목",
        "meeting_date": "2025-11-10",
        "audio_file": "uuid.mp3",
        "main_topic": "주제 제목",
        "summary_index": 0
    },
    "embedding": [0.1, 0.2, ...]
}
```

---

## Q20. 스마트 청킹 알고리즘은 어떻게 작동하나요?

**A20.** 3가지 조건으로 청크를 분리합니다:

1. **크기 초과**: 1000자 초과 시 무조건 분리
2. **시간 간격**: 60초 이상 침묵 + 200자 이상
3. **화자 변경**: 화자 바뀜 + 500자 이상

코드 위치: `utils/vector_db_manager.py:230-308`

---

## Q21. 청킹 시 텍스트 정제는 어떻게 하나요?

**A21.** 정규표현식으로 화자/시간 정보를 제거합니다:

**입력**:
```
[Speaker 1, 00:30] 안녕하세요. 회의를 시작하겠습니다.
[Speaker 2, 00:45] 네, 알겠습니다.
```

**출력**:
```
안녕하세요. 회의를 시작하겠습니다.
네, 알겠습니다.
```

패턴: `\[Speaker [^,]+, \d{2}:\d{2}\]\s*`

---

## Q22. 임베딩은 어떻게 생성하나요?

**A22.** OpenAI의 text-embedding-3-small 모델을 사용합니다:

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# 텍스트 → 1536차원 벡터
vector = embeddings.embed_query("안녕하세요")
# [0.023, -0.145, 0.678, ...]
```

---

## Q23. SQLite와 ChromaDB의 역할 분담은?

**A23.** 다음과 같이 구분됩니다:

**SQLite** (관계형 DB):
- 메타데이터 저장 (제목, 날짜, 소유자)
- 사용자 정보
- 공유 관계
- 빠른 필터링 (인덱스 활용)

**ChromaDB** (벡터 DB):
- 실제 텍스트 내용 저장
- 의미론적 검색 (유사도 기반)
- 임베딩 벡터 저장

---

## Q24. 데이터베이스 인덱스는 어떻게 설정되어 있나요?

**A24.** 다음 인덱스들이 설정되어 있습니다:

```sql
-- 회의 조회 최적화
CREATE INDEX idx_meetings_owner ON meetings(owner_id);
CREATE INDEX idx_meetings_date ON meetings(meeting_date DESC);

-- 대화 조회 최적화
CREATE INDEX idx_dialogues_meeting ON meeting_dialogues(meeting_id);
CREATE INDEX idx_dialogues_time ON meeting_dialogues(start_time);

-- 공유 확인 최적화
CREATE INDEX idx_shares_user ON meeting_shares(shared_with_user_id);
```

---

## Q25. 데이터베이스 연결은 어떻게 관리하나요?

**A25.** 매 요청마다 새 연결을 생성합니다 (Thread-safe):

```python
def _get_connection(self):
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row  # Dict처럼 사용
    return conn
```

Context Manager 사용으로 자동 종료:
```python
with self._get_connection() as conn:
    conn.execute("SELECT * FROM meetings")
```

---

## Q26. FK CASCADE는 어떻게 동작하나요?

**A26.** meetings 테이블 삭제 시 관련 데이터가 자동 삭제됩니다:

```sql
DELETE FROM meetings WHERE id = 'uuid';

-- 자동으로 삭제되는 것들:
-- 1. meeting_dialogues (모든 대화)
-- 2. meeting_minutes (회의록)
-- 3. meeting_shares (공유 정보)
```

---

## Q27. 회의 정보는 어떻게 저장하나요?

**A27.** `db_manager.py`의 `save_meeting_info()` 메서드를 사용합니다:

```python
db.save_meeting_info(
    meeting_id=str(uuid.uuid4()),
    title="1차회의",
    meeting_date=datetime.now(),
    audio_file="uuid_audio.mp3",
    owner_id=user_id
)
```

---

## Q28. 대화 내용은 어떻게 저장하나요?

**A28.** `save_segment()` 메서드로 한 줄씩 저장합니다:

```python
for seg in segments:
    db.save_segment(
        meeting_id=meeting_id,
        speaker_label=seg['speaker_label'],
        start_time=seg['start_time'],
        segment=seg['segment'],
        confidence=seg['confidence']
    )
```

---

## Q29. 특정 회의의 모든 대화를 조회하려면?

**A29.** 다음 쿼리를 사용합니다:

```python
dialogues = db.execute("""
    SELECT speaker_label, start_time, segment
    FROM meeting_dialogues
    WHERE meeting_id = ?
    ORDER BY start_time ASC
""", (meeting_id,))
```

---

## Q30. 벡터 DB에서 검색은 어떻게 하나요?

**A30.** `vector_db_manager.py`의 `search()` 메서드를 사용합니다:

```python
results = vdb_manager.search(
    db_type="chunks",           # 또는 "subtopic"
    query="다음 회의 일정은?",
    k=3,                        # 상위 3개
    retriever_type="similarity",
    filter_criteria={"meeting_id": "uuid"}  # optional
)
```

---

# 3부. 백엔드 모듈

## Q31. STTManager의 주요 역할은?

**A31.** 3가지 주요 기능을 담당합니다:

1. **음성 인식** (`transcribe_audio()`): Gemini Pro로 STT + 화자 분리
2. **요약 생성** (`subtopic_generate()`): Gemini Flash로 주제별 요약
3. **마인드맵 생성** (`extract_mindmap_keywords()`): 마크다운 마인드맵

코드 위치: `utils/stt.py`

---

## Q32. STT는 어떻게 실행하나요?

**A32.** `utils/stt.py:29-152`에서 실행됩니다:

```python
def transcribe_audio(self, audio_path, original_filename):
    # 1. 파일 읽기
    with open(audio_path, "rb") as f:
        file_bytes = f.read()

    # 2. MIME 타입 결정
    mime_type = "audio/wav"  # 또는 mp3, m4a 등

    # 3. Gemini API 호출
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[prompt, types.Part.from_bytes(data=file_bytes, mime_type=mime_type)]
    )

    # 4. JSON 파싱
    result_list = json.loads(response.text)

    return normalized_segments
```

---

## Q33. STT 프롬프트의 핵심 지침은?

**A33.** 다음과 같습니다:

1. **충실도 우선**: 실제 발화 내용만 인식
2. **금지 사항**: 문장 보정, 동사 생성/보정, 불필요한 단어 추가
3. **화자 분리**: 동일 화자는 같은 번호 유지
4. **겹침 처리**: 동시 발화는 각각 시간 기록
5. **JSON 출력**: 파싱 가능한 형식

---

## Q34. STT 출력 형식은?

**A34.** 다음과 같은 JSON 배열입니다:

```json
[
    {
        "speaker": 1,
        "start_time_mmss": "0:00:000",
        "confidence": 0.95,
        "text": "안녕하세요. 회의를 시작하겠습니다."
    },
    {
        "speaker": 2,
        "start_time_mmss": "0:15:500",
        "confidence": 0.92,
        "text": "네, 알겠습니다."
    }
]
```

---

## Q35. 요약은 어떻게 생성하나요?

**A35.** `utils/stt.py:154-271`에서 Gemini Flash를 사용합니다:

**출력 형식**:
```markdown
### 첫 번째 주요 주제
* 첫 번째 논의 내용 요약 [cite: 1]
* 두 번째 논의 내용 요약 [cite: 2, 3]

### 두 번째 주요 주제
* 세 번째 논의 내용 요약 [cite: 4]
```

**핵심 규칙**:
- 주제별 그룹화
- `### 제목` 형식 필수
- 구어체 → 문어체 변환
- 화자 라벨 제거

---

## Q36. 마인드맵은 어떻게 생성하나요?

**A36.** `utils/stt.py:432-526`에서 Gemini Flash를 사용합니다:

**출력 형식**:
```markdown
# 1차회의
## 주요 안건
### 프로젝트 일정
- 11월 15일 완료
### 예산
- 20만원
```

**핵심 규칙**:
- 최상위(#)는 회의 제목만
- 2단계(##)부터 실제 주제
- 최대 깊이 4단계(####)

---

## Q37. DatabaseManager의 주요 메서드는?

**A37.** 다음과 같습니다:

- `save_meeting_info()`: 회의 정보 저장
- `save_segment()`: 대화 내용 저장
- `save_minutes()`: 회의록 저장
- `get_meeting_by_id()`: 회의 조회
- `get_dialogues_by_meeting()`: 대화 조회
- `delete_meeting()`: 회의 삭제 (Cascade)

코드 위치: `utils/db_manager.py`

---

## Q38. VectorDBManager의 주요 메서드는?

**A38.** 다음과 같습니다:

- `add_meeting_as_chunk()`: 청킹 후 저장
- `add_summary_as_subtopic()`: 요약 저장
- `search()`: 벡터 검색
- `delete_from_collection()`: 벡터 삭제
- `_create_smart_chunks()`: 스마트 청킹 알고리즘

코드 위치: `utils/vector_db_manager.py`

---

## Q39. ChatManager의 주요 역할은?

**A39.** RAG 챗봇 엔진 역할을 합니다:

1. **문서 검색** (`search_documents()`): chunks + subtopics 이중 검색
2. **컨텍스트 생성** (`format_context()`): 검색 결과를 프롬프트 형식으로 변환
3. **답변 생성** (`generate_answer()`): Gemini로 답변
4. **전체 파이프라인** (`process_query()`): 1~3 통합 실행

코드 위치: `utils/chat_manager.py`

---

## Q40. RAG 파이프라인은 어떻게 동작하나요?

**A40.** 다음 4단계로 동작합니다:

1. **검색**: chunks 3개 + subtopics 3개
2. **컨텍스트 생성**: 검색 결과를 프롬프트로 포맷팅
3. **답변 생성**: Gemini에 프롬프트 전송
4. **출처 추가**: sources 배열에 메타데이터 포함

```python
result = chat_manager.process_query(
    query="다음 회의 일정은?",
    meeting_id="uuid",
    accessible_meeting_ids=None
)
```

---

## Q41. 챗봇은 어떻게 이중 검색을 하나요?

**A41.** chunks와 subtopics에서 각각 3개씩 검색합니다:

```python
# 1. chunks 검색 (실제 대화)
chunks = vdb_manager.search("chunks", query, k=3, filter_criteria={"meeting_id": meeting_id})

# 2. subtopics 검색 (요약)
subtopics = vdb_manager.search("subtopic", query, k=3, filter_criteria={"meeting_id": meeting_id})

return {
    "chunks": chunks,
    "subtopics": subtopics,
    "total_count": 6
}
```

---

## Q42. 전체 노트 검색은 어떻게 하나요?

**A42.** 다음과 같이 처리합니다:

1. 넉넉하게 k=30 검색
2. Python에서 `accessible_meeting_ids`로 필터링
3. 상위 3개씩 선택

```python
chunk_result = vdb_manager.search("chunks", query, k=30)

# 권한 필터링
chunks = [doc for doc in chunk_result
         if doc.metadata['meeting_id'] in accessible_meeting_ids]

# 상위 3개
chunks = chunks[:3]
```

---

## Q43. 챗봇 컨텍스트는 어떻게 포맷팅하나요?

**A43.** 다음 형식으로 변환합니다:

```
=== 회의 대화 내용 ===
[문서 1]
회의: 1차회의
일시: 2025-11-10
시간: 120초 - 180초
내용:
다음 회의는 15일로 결정되었습니다.

=== 회의 주제별 요약 ===
[요약 1]
회의: 1차회의
주제: 일정 논의
내용:
### 일정 논의
* 다음 회의 15일 확정
```

---

## Q44. 챗봇 답변 생성 프롬프트는?

**A44.** 다음과 같습니다:

```
당신은 회의록 챗봇입니다.

[핵심 지침]
1. **반드시** 아래 [검색된 회의록 내용] **안에서만** 정보를 찾아서 답변
2. 정보가 없다면 "해당 내용을 회의록에서 찾을 수 없습니다."
3. 절대로 사전 지식이나 외부 정보 사용 금지
4. 답변은 명확하고 간결하게
5. **중요**: 회의 제목과 날짜는 메타데이터 참조

[검색된 회의록 내용]:
{context}

[사용자 질문]:
{query}

[답변]:
```

---

## Q45. 할루시네이션 방지 전략은?

**A45.** 다음 전략을 사용합니다:

1. **명시적 제한**: "반드시 검색 결과 안에서만"
2. **솔직한 답변**: 정보 없으면 "모른다" 답변
3. **외부 지식 금지**: 명시적으로 금지 명령
4. **메타데이터 우선**: 본문의 잘못된 정보 무시

---

## Q46. UserManager의 주요 역할은?

**A46.** 사용자 및 권한 관리를 담당합니다:

- `get_or_create_user()`: 사용자 조회/생성
- `can_access_meeting()`: 접근 권한 체크
- `get_user_accessible_meeting_ids()`: 접근 가능한 회의 목록
- `share_meeting()`: 회의록 공유
- `is_admin()`: 관리자 확인

코드 위치: `utils/user_manager.py`

---

## Q47. 접근 권한 체크는 어떻게 하나요?

**A47.** 3가지 조건 중 하나라도 만족하면 허용:

```python
def can_access_meeting(user_id, meeting_id):
    # 1. 본인 소유
    meeting = db.execute("SELECT owner_id FROM meetings WHERE id = ?", (meeting_id,))
    if meeting and meeting['owner_id'] == user_id:
        return True

    # 2. 공유받음
    share = db.execute("""
        SELECT 1 FROM meeting_shares
        WHERE meeting_id = ? AND shared_with_user_id = ?
    """, (meeting_id, user_id))
    if share:
        return True

    # 3. 관리자
    if is_admin(user_id):
        return True

    return False
```

---

## Q48. 접근 가능한 회의 목록은 어떻게 조회하나요?

**A48.** 다음과 같이 조회합니다:

```python
def get_user_accessible_meeting_ids(user_id):
    # 1. 본인 소유
    owned = db.execute(
        "SELECT id FROM meetings WHERE owner_id = ?",
        (user_id,)
    ).fetchall()

    # 2. 공유받음
    shared = db.execute("""
        SELECT meeting_id FROM meeting_shares
        WHERE shared_with_user_id = ?
    """, (user_id,)).fetchall()

    # 3. 합치기
    meeting_ids = [row['id'] for row in owned] + [row['meeting_id'] for row in shared]
    return list(set(meeting_ids))  # 중복 제거
```

---

## Q49. 회의록 공유는 어떻게 하나요?

**A49.** `share_meeting()` 메서드를 사용합니다:

```python
def share_meeting(meeting_id, owner_id, target_email, permission='read'):
    # 1. 권한 체크
    if not can_edit_meeting(owner_id, meeting_id):
        raise PermissionError("공유 권한 없음")

    # 2. 대상 사용자 조회
    target_user = db.execute(
        "SELECT id FROM users WHERE email = ?",
        (target_email,)
    ).fetchone()

    # 3. 공유 등록
    db.execute("""
        INSERT OR IGNORE INTO meeting_shares
        (meeting_id, shared_with_user_id, permission)
        VALUES (?, ?, ?)
    """, (meeting_id, target_user['id'], permission))
```

---

## Q50. 관리자는 어떻게 확인하나요?

**A50.** `.env` 파일의 `ADMIN_EMAILS`로 확인합니다:

```python
def is_admin(user_id):
    user = db.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return False

    admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")
    return user['email'] in admin_emails
```

예: `ADMIN_EMAILS=admin@example.com,boss@example.com`

---

# 4부. API 엔드포인트

## Q51. 로그인 API는 어떻게 동작하나요?

**A51.** POST `/api/login`으로 Firebase ID 토큰을 검증합니다:

**Request**:
```json
{
    "idToken": "Firebase_ID_Token"
}
```

**Response**:
```json
{
    "success": true,
    "user": {
        "uid": "firebase_uid",
        "email": "user@example.com",
        "displayName": "홍길동"
    }
}
```

---

## Q52. 파일 업로드 API의 Request 형식은?

**A52.** POST `/api/upload`에 FormData로 전송합니다:

```javascript
FormData {
    "title": "1차회의",
    "meeting_date": "2025-11-10",
    "audio_file": File  // wav, mp3, m4a, flac, mp4
}
```

---

## Q53. 파일 업로드 API의 Response 형식은?

**A53.** 다음과 같습니다:

**성공**:
```json
{
    "success": true,
    "meeting_id": "uuid",
    "redirect_url": "/viewer/uuid"
}
```

**실패**:
```json
{
    "success": false,
    "error": "제목은 1~100자 이내여야 합니다"
}
```

---

## Q54. SSE 진행률 API는 어떻게 사용하나요?

**A54.** POST `/api/upload_with_progress`를 사용합니다:

**Response** (text/event-stream):
```
data: {"progress": 20, "message": "파일 저장 완료"}

data: {"progress": 40, "message": "음성 인식 중..."}

data: {"progress": 60, "message": "DB 저장 중..."}

data: {"progress": 100, "message": "완료!"}
```

---

## Q55. 회의 정보 조회 API는?

**A55.** GET `/api/meeting/<meeting_id>`를 사용합니다:

**Response**:
```json
{
    "id": "uuid",
    "title": "1차회의",
    "meeting_date": "2025-11-10",
    "audio_file": "uuid_audio.mp3",
    "owner_id": 1,
    "created_at": "2025-11-10 10:00:00"
}
```

---

## Q56. 제목 수정 API는?

**A56.** POST `/api/update_title/<meeting_id>`를 사용합니다:

**Request**:
```json
{
    "new_title": "수정된 제목"
}
```

**Response**:
```json
{
    "success": true,
    "message": "제목이 수정되었습니다"
}
```

---

## Q57. 회의 삭제 API는?

**A57.** POST `/api/delete_meeting/<meeting_id>`를 사용합니다:

**Response**:
```json
{
    "success": true,
    "message": "회의 데이터가 삭제되었습니다",
    "deleted": {
        "sqlite_dialogues": 50,
        "sqlite_minutes": 1,
        "sqlite_shares": 2,
        "vector_chunks": 15,
        "vector_subtopic": 5,
        "audio_file": "uuid_audio.mp3"
    }
}
```

삭제 범위: SQLite + ChromaDB + 오디오 파일 (Cascade)

---

## Q58. 챗봇 API의 Request 형식은?

**A58.** POST `/api/chat`에 다음 형식으로 전송합니다:

```json
{
    "query": "다음 회의 일정은?",
    "meeting_id": "uuid"  // optional (null이면 전체 검색)
}
```

---

## Q59. 챗봇 API의 Response 형식은?

**A59.** 다음과 같습니다:

```json
{
    "success": true,
    "answer": "11월 15일입니다.",
    "sources": [
        {
            "type": "chunk",
            "meeting_id": "uuid",
            "title": "1차회의",
            "meeting_date": "2025-11-10",
            "start_time": 120,
            "end_time": 180
        },
        {
            "type": "subtopic",
            "meeting_id": "uuid",
            "meeting_title": "1차회의",
            "main_topic": "일정 논의"
        }
    ]
}
```

---

## Q60. 회의록 공유 API는?

**A60.** POST `/api/share/<meeting_id>`를 사용합니다:

**Request**:
```json
{
    "email": "friend@example.com",
    "permission": "read"  // "read", "write", "admin"
}
```

**Response**:
```json
{
    "success": true,
    "message": "회의록이 공유되었습니다"
}
```

---

## Q61. 공유 취소 API는?

**A61.** POST `/api/unshare/<meeting_id>/<user_id>`를 사용합니다:

**Response**:
```json
{
    "success": true,
    "message": "공유가 취소되었습니다"
}
```

---

## Q62. 공유 목록 조회 API는?

**A62.** GET `/api/shared_users/<meeting_id>`를 사용합니다:

**Response**:
```json
{
    "success": true,
    "shared_users": [
        {
            "user_id": 2,
            "email": "friend@example.com",
            "display_name": "김철수",
            "permission": "read",
            "shared_at": "2025-11-10 15:00:00"
        }
    ]
}
```

---

## Q63. 에러 응답 형식은?

**A63.** 다음과 같습니다:

**400 Bad Request**:
```json
{
    "success": false,
    "error": "제목이 비어있습니다"
}
```

**403 Forbidden**:
```json
{
    "success": false,
    "error": "접근 권한이 없습니다"
}
```

**404 Not Found**:
```json
{
    "error": "Not found"
}
```

**500 Internal Server Error**:
```json
{
    "error": "Internal server error"
}
```

---

## Q64. 인증이 필요한 API는?

**A64.** 로그인 관련을 제외한 모든 API가 인증이 필요합니다:

**인증 불필요**:
- `/login`
- `/api/login`

**인증 필요** (@login_required):
- `/`
- `/api/upload`
- `/api/chat`
- `/api/delete_meeting/<meeting_id>`
- 기타 모든 API

---

## Q65. 인증은 어떻게 처리하나요?

**A65.** Flask 세션을 사용합니다:

```python
# 로그인 시
session['user_id'] = user_id
session['firebase_uid'] = firebase_uid

# 인증 확인 (decorators.py)
@login_required
def protected_route():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
```

---

# 5부. 실전 프로세스

## Q66. 회의록 생성 전체 프로세스를 설명해주세요.

**A66.** 11단계 파이프라인입니다:

1. 파일 업로드 (FormData)
2. 검증 및 저장 (uploads/)
3. MP4 변환 (필요시)
4. STT 실행 (Gemini Pro)
5. SQLite 저장 (meetings, meeting_dialogues)
6. 스마트 청킹
7. ChromaDB 저장 (meeting_chunks)
8. 요약 생성 (Gemini Flash)
9. ChromaDB 저장 (meeting_subtopic)
10. 마인드맵 생성
11. SQLite 저장 (meeting_minutes)

**소요 시간** (30분 회의): 약 4분

---

## Q67. 파일 검증은 어떻게 하나요?

**A67.** 다음을 검증합니다:

1. **제목**: 1~100자, 특수문자 제한
2. **날짜**: ISO 8601 형식
3. **파일**: 확장자 화이트리스트 (wav, mp3, m4a, flac, mp4)
4. **크기**: 500MB 이하

코드 위치: `utils/validation.py`

---

## Q68. MP4 변환은 어떻게 하나요?

**A68.** ffmpeg로 오디오 트랙만 추출합니다:

```python
def convert_video_to_audio(video_path, audio_path):
    command = [
        'ffmpeg',
        '-i', video_path,
        '-vn',                    # 비디오 제거
        '-acodec', 'pcm_s16le',   # WAV 코덱
        '-ar', '44100',           # 샘플링 레이트
        '-ac', '2',               # 스테레오
        audio_path
    ]
    subprocess.run(command, check=True)
```

---

## Q69. 챗봇 질의 전체 프로세스를 설명해주세요.

**A69.** 8단계 파이프라인입니다:

1. 질문 수신 (POST /api/chat)
2. 권한 체크 (can_access_meeting)
3. ChatManager 호출
4. 쿼리 임베딩 (OpenAI)
5. 이중 검색 (chunks + subtopics)
6. 컨텍스트 포맷팅
7. Gemini 답변 생성
8. 출처 정보 추가 및 응답

**소요 시간**: 약 3.77초

---

## Q70. 챗봇 검색은 단일 노트와 전체 노트가 어떻게 다른가요?

**A70.** 다음과 같이 다릅니다:

**단일 노트 검색**:
- `meeting_id`로 필터링
- 각 컬렉션에서 k=3 검색
- ChromaDB 레벨 필터링

**전체 노트 검색**:
- k=30으로 넉넉하게 검색
- Python에서 `accessible_meeting_ids`로 필터링
- 상위 3개씩 선택

---

## Q71. 회의록 삭제 전체 프로세스를 설명해주세요.

**A71.** 7단계 프로세스입니다:

1. 삭제 요청 (POST /api/delete_meeting)
2. 권한 체크
3. VectorDBManager 통합 삭제 호출
4. ChromaDB 삭제 (chunks + subtopic)
5. SQLite 삭제 (meetings → CASCADE)
6. 오디오 파일 삭제
7. 결과 응답

**삭제 범위**: 5개 테이블 + 2개 컬렉션 + 파일

---

## Q72. CASCADE 삭제는 어떻게 동작하나요?

**A72.** meetings 테이블 삭제 시 FK로 연결된 모든 데이터가 자동 삭제됩니다:

```sql
DELETE FROM meetings WHERE id = 'uuid';

-- 자동 삭제:
-- 1. meeting_dialogues (ON DELETE CASCADE)
-- 2. meeting_minutes (ON DELETE CASCADE)
-- 3. meeting_shares (ON DELETE CASCADE)
```

---

## Q73. 파일 업로드 중 에러가 발생하면?

**A73.** 다음과 같이 처리합니다:

1. **STT 실패**: 폴백 모드 (기본 청킹)
2. **DB 저장 실패**: 트랜잭션 롤백
3. **임베딩 실패**: 재시도 로직 (최대 3회)
4. **사용자에게 명확한 에러 메시지 반환**

---

## Q74. 챗봇이 답변을 찾지 못하면?

**A74.** 다음과 같이 응답합니다:

```json
{
    "success": true,
    "answer": "죄송합니다. 해당 내용을 회의록에서 찾을 수 없습니다.",
    "sources": []
}
```

할루시네이션 방지를 위해 정보가 없으면 솔직히 "모른다"고 답변합니다.

---

## Q75. 실시간 진행률은 어떻게 표시하나요?

**A75.** SSE (Server-Sent Events)를 사용합니다:

```python
def generate():
    yield f"data: {json.dumps({'progress': 20, 'message': '파일 저장 완료'})}\n\n"
    # STT 실행
    yield f"data: {json.dumps({'progress': 40, 'message': '음성 인식 중...'})}\n\n"
    # ... 계속

return Response(stream_with_context(generate()), mimetype='text/event-stream')
```

---

## Q76. 회의록 제목 수정 시 어디가 업데이트되나요?

**A76.** 3곳이 업데이트됩니다:

1. **SQLite meetings 테이블**
2. **ChromaDB meeting_chunks** (metadata.title)
3. **ChromaDB meeting_subtopic** (metadata.meeting_title)

코드 위치: `utils/vector_db_manager.py:857-958`

---

## Q77. 공유받은 회의록을 수정할 수 있나요?

**A77.** permission에 따라 다릅니다:

- **read**: 조회만 가능
- **write**: 제목 수정 가능
- **admin**: 삭제 및 재공유 가능

권한 체크는 `can_edit_meeting()` 함수에서 수행됩니다.

---

## Q78. 여러 사용자가 동시에 같은 회의록을 조회하면?

**A78.** 문제없이 동작합니다:

- SQLite: 매 요청마다 새 연결 (Thread-safe)
- ChromaDB: Read 작업은 Lock 불필요
- 세션: 사용자별로 독립적

---

## Q79. 회의록 생성 중 서버가 종료되면?

**A79.** 다음과 같이 처리됩니다:

1. **트랜잭션 미완료**: 롤백 (데이터 일관성 유지)
2. **파일 업로드 완료**: uploads/ 폴더에 남음 (수동 삭제 필요)
3. **부분 완료 데이터**: 다음 요청 시 정리 가능

향후 개선: Redis Queue로 백그라운드 작업 처리

---

## Q80. 대용량 파일 (1시간 회의) 처리는?

**A80.** 다음과 같이 처리합니다:

- **STT**: 약 5-10분 소요
- **청킹**: 약 1-2분
- **임베딩**: 배치 처리로 2-3분
- **총 소요 시간**: 약 10-15분

현재 제한: 500MB (약 2시간 회의)

---

# 6부. 최적화 & 보안

## Q81. 데이터베이스 쿼리 최적화 팁은?

**A81.** 다음을 권장합니다:

**나쁜 예**:
```python
# Python에서 필터링
meetings = db.execute("SELECT * FROM meetings")
my_meetings = [m for m in meetings if m['owner_id'] == user_id]
```

**좋은 예**:
```python
# DB에서 필터링
my_meetings = db.execute(
    "SELECT * FROM meetings WHERE owner_id = ? ORDER BY meeting_date DESC",
    (user_id,)
)
```

---

## Q82. 인덱스는 언제 추가해야 하나요?

**A82.** 다음 경우에 추가합니다:

1. **WHERE 절에 자주 사용되는 컬럼**
2. **ORDER BY에 사용되는 컬럼**
3. **JOIN에 사용되는 컬럼**
4. **GROUP BY에 사용되는 컬럼**

예: `CREATE INDEX idx_meetings_date ON meetings(meeting_date DESC);`

---

## Q83. ChromaDB 검색 최적화 방법은?

**A83.** 다음을 권장합니다:

1. **메타데이터 필터링 활용**: Python 필터링보다 DB 레벨 필터링
2. **배치 임베딩**: 하나씩 대신 배치로 처리 (10배 빠름)
3. **캐싱**: 동일 쿼리는 결과 캐싱
4. **k 값 조정**: 필요한 만큼만 검색

---

## Q84. 배치 임베딩은 어떻게 하나요?

**A84.** 다음과 같이 합니다:

**나쁜 예**:
```python
for chunk in chunks:
    embedding = embeddings.embed_query(chunk['text'])
```

**좋은 예**:
```python
texts = [chunk['text'] for chunk in chunks]
embeddings_list = embeddings.embed_documents(texts)  # 10배 빠름
```

---

## Q85. SQL Injection은 어떻게 방지하나요?

**A85.** Parameterized Query를 사용합니다:

**나쁜 예**:
```python
query = f"SELECT * FROM meetings WHERE id = '{meeting_id}'"  # 위험!
```

**좋은 예**:
```python
query = "SELECT * FROM meetings WHERE id = ?"
db.execute(query, (meeting_id,))  # 안전
```

---

## Q86. XSS 공격은 어떻게 방지하나요?

**A86.** 다음 방법을 사용합니다:

1. **Jinja2 자동 이스케이프** (Flask 기본):
```html
{{ user_input }}  <!-- 자동으로 HTML escape -->
```

2. **마크다운 Sanitize**:
```python
import bleach
safe_html = bleach.clean(markdown_html, tags=['p', 'h1', 'h2', 'ul', 'li'])
```

---

## Q87. 파일 업로드 보안은 어떻게 하나요?

**A87.** 다음을 적용합니다:

1. **확장자 화이트리스트**:
```python
ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "flac", "mp4"}
```

2. **파일 크기 제한**:
```python
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
```

3. **파일명 안전화**:
```python
filename = secure_filename(file.filename)
unique_filename = f"{uuid.uuid4().hex}_{filename}"
```

4. **MIME 타입 검증** (향후 추가)

---

## Q88. 세션 보안은 어떻게 설정하나요?

**A88.** 다음과 같이 설정합니다:

```python
app.config['SESSION_COOKIE_SECURE'] = True      # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True    # JavaScript 접근 차단
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF 방지
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
```

---

## Q89. 에러 핸들링은 어떻게 하나요?

**A89.** 전역 에러 핸들러를 사용합니다:

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({"error": "An unexpected error occurred"}), 500
```

---

## Q90. 재시도 로직은 어떻게 구현하나요?

**A90.** tenacity 라이브러리를 사용합니다:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def transcribe_audio(audio_path):
    """최대 3회 재시도 (지수 백오프: 4초, 8초, 10초)"""
    return gemini_api_call(audio_path)
```

---

## Q91. 로깅은 어떻게 설정하나요?

**A91.** 다음과 같이 설정합니다:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 사용 예시
logger.info(f"User {user_id} uploading file")
logger.error(f"Upload failed: {e}", exc_info=True)
```

---

## Q92. 성능 모니터링은 어떻게 하나요?

**A92.** 데코레이터를 사용합니다:

```python
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} took {end - start:.2f}s")
        return result
    return wrapper

@timing_decorator
def transcribe_audio(audio_path):
    pass  # 실행 시간 자동 로깅
```

---

## Q93. API Rate Limiting은?

**A93.** Flask-Limiter를 사용할 수 있습니다 (향후 추가):

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    default_limits=["200 per hour", "50 per minute"]
)

@app.route("/api/chat")
@limiter.limit("10 per minute")
def chat():
    pass
```

---

## Q94. 타임아웃은 어떻게 설정하나요?

**A94.** API 호출 시 타임아웃을 설정합니다:

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    request_options={"timeout": 30}  # 30초
)
```

---

## Q95. Connection Pool은?

**A95.** 향후 SQLAlchemy로 개선 예정입니다:

```python
from sqlalchemy import create_engine

engine = create_engine(
    'sqlite:///minute_ai.db',
    pool_size=10,
    max_overflow=20
)
```

현재는 매 요청마다 새 연결 생성 (Thread-safe)

---

## Q96. 임베딩 캐싱은?

**A96.** 향후 개선 예정입니다:

```python
embedding_cache = {}

def get_embedding(text):
    if text in embedding_cache:
        return embedding_cache[text]

    embedding = embeddings.embed_query(text)
    embedding_cache[text] = embedding
    return embedding
```

---

## Q97. 민감 정보는 어떻게 관리하나요?

**A97.** 환경 변수로 관리합니다:

```.env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
FLASK_SECRET_KEY=...
FIREBASE_API_KEY=...
ADMIN_EMAILS=admin@example.com
```

절대로 코드에 하드코딩하지 않습니다!

---

## Q98. 백업 전략은?

**A98.** 다음을 백업합니다:

1. **SQLite**: `database/minute_ai.db`
2. **ChromaDB**: `database/vector_db/` 폴더 전체
3. **업로드 파일**: `uploads/` 폴더 전체
4. **환경 변수**: `.env` 파일 (암호화 필요)

주기: 매일 자동 백업 권장

---

## Q99. 프로덕션 배포 시 체크리스트는?

**A99.** 다음을 확인합니다:

- [ ] DEBUG = False
- [ ] SECRET_KEY 변경
- [ ] 환경 변수 설정
- [ ] HTTPS 설정
- [ ] 방화벽 설정
- [ ] 로깅 설정
- [ ] 백업 설정
- [ ] 모니터링 설정
- [ ] 에러 알림 설정

---

## Q100. 향후 개선 계획은?

**A100.** 다음을 계획 중입니다:

1. **Connection Pool**: SQLAlchemy 도입
2. **Redis**: 임베딩 캐싱, 세션 저장
3. **Celery**: 백그라운드 작업 큐
4. **Rate Limiting**: API 호출 제한
5. **MIME 검증**: 파일 타입 엄격한 검증
6. **모니터링**: Prometheus + Grafana
7. **CI/CD**: GitHub Actions
8. **테스트**: Pytest 추가

---

# 부록

## 주요 파일 참조표

| 파일 | 핵심 라인 | 설명 |
|------|----------|------|
| app.py | 392-554 | 파일 업로드 & 파이프라인 |
| app.py | 1112-1165 | 챗봇 API |
| utils/stt.py | 29-152 | Gemini STT |
| utils/stt.py | 154-271 | 요약 생성 |
| utils/stt.py | 432-526 | 마인드맵 생성 |
| utils/db_manager.py | 전체 | SQLite CRUD |
| utils/vector_db_manager.py | 116-171 | 청킹 & 저장 |
| utils/vector_db_manager.py | 230-310 | 스마트 청킹 |
| utils/vector_db_manager.py | 368-483 | 벡터 검색 |
| utils/chat_manager.py | 319-387 | RAG 파이프라인 |
| utils/user_manager.py | 137-165 | 권한 체크 |

---

## 핵심 개념 요약

### 데이터 흐름
```
파일 → STT → SQLite + ChromaDB → 요약/마인드맵 → 완료
```

### RAG 파이프라인
```
질문 → 임베딩 → 벡터 검색 → 컨텍스트 → Gemini → 답변
```

### 권한 체계
```
본인 소유 OR 공유받음 OR 관리자 = 접근 허용
```

### 데이터베이스
- **SQLite**: 메타데이터 (5개 테이블)
- **ChromaDB**: 실제 내용 (2개 컬렉션)

### AI 역할
- **Gemini Pro**: STT (화자 분리)
- **Gemini Flash**: 요약, 마인드맵, 챗봇
- **OpenAI**: 임베딩 (1536차원)

---

**작성일**: 2025-11-11
**버전**: Q&A 인쇄용 v1.0
**총 문항**: 100개
**예상 페이지**: 약 50페이지

이 문서 하나면 백엔드 시스템을 완벽히 이해할 수 있습니다!
