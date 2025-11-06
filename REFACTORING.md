# Minute AI - 리팩토링 가이드

## 📅 작성일: 2025-11-06

---

## 📊 현재 코드 평가

### 종합 점수: **6.2/10**

| 항목 | 점수 | 평가 |
|------|------|------|
| **기능 구현** | 9/10 | 모든 핵심 기능 완성 |
| **모듈화** | 7/10 | utils 분리는 좋으나 app.py가 비대 |
| **코드 가독성** | 7/10 | 주석은 있으나 함수가 너무 김 |
| **에러 처리** | 6/10 | 기본적 처리는 있으나 구체성 부족 |
| **확장성** | 5/10 | Blueprint, Service Layer 없음 |
| **테스트** | 0/10 | 테스트 코드 없음 |
| **성능** | 6/10 | 동기 처리로 블로킹 이슈 |
| **보안** | 7/10 | Firebase 인증은 좋으나 권한 체크 미흡 |
| **문서화** | 9/10 | next.md가 매우 상세 |

**결론**: "**작동하는 프로토타입**" 수준
- ✅ 기능은 완성되었고, 데모/개인 사용에는 충분
- ⚠️ 프로덕션 배포나 팀 협업에는 리팩토링 필요

---

## ✅ 잘 구성된 부분

### 1. 명확한 모듈 분리
```
utils/
  ├── stt.py              # STT 전담
  ├── db_manager.py       # DB 작업 전담
  ├── vector_db_manager.py # Vector DB 전담
  ├── chat_manager.py     # 챗봇 로직 분리
  └── user_manager.py     # 사용자 관리 분리
```
- 관심사 분리(Separation of Concerns)가 잘 되어 있음
- 각 모듈의 책임이 명확함

### 2. 우수한 문서화
- `next.md`가 매우 상세함 (1100+ 줄)
- 삭제 검증 로그가 터미널에 상세하게 출력됨
- 주석이 적절히 있음

### 3. 합리적인 기술 스택 선택
- SQLite (관계형) + ChromaDB (벡터) 조합이 적절
- Gemini 2.5 Pro로 STT부터 요약까지 일관성 있음
- Firebase Authentication 통합이 깔끔함

### 4. 에러 처리가 기본적으로 존재
```python
try:
    # 작업 수행
except Exception as e:
    return jsonify({"error": f"오류: {e}"}), 500
```

---

## ⚠️ 개선이 필요한 부분

### 1. app.py가 너무 비대함 (957줄) 🔴 High Priority

**현재 문제**:
```python
# app.py에 모든 라우트가 집중되어 있음 (957줄)
@app.route("/upload", methods=["POST"])  # 150줄
@app.route("/api/chat", methods=["POST"])  # 50줄
@app.route("/api/generate_minutes/<meeting_id>", methods=["POST"])  # 50줄
# ... 20개 이상의 라우트
```

**개선 방안**: Flask Blueprint로 분리

```python
# blueprints/auth.py
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login")
def login_page():
    # 로그인 페이지
    pass

@auth_bp.route("/api/login", methods=["POST"])
def login():
    # 로그인 처리
    pass

@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    # 로그아웃 처리
    pass
```

```python
# blueprints/upload.py
from flask import Blueprint

upload_bp = Blueprint('upload', __name__)

@upload_bp.route("/upload", methods=["POST"])
def upload_and_process():
    # 업로드 처리
    pass

@upload_bp.route("/upload_script", methods=["POST"])
def upload_script():
    # 스크립트 업로드
    pass
```

```python
# blueprints/meeting.py
from flask import Blueprint

meeting_bp = Blueprint('meeting', __name__)

@meeting_bp.route("/view/<string:meeting_id>")
def view_meeting(meeting_id):
    pass

@meeting_bp.route("/api/meeting/<string:meeting_id>")
def get_meeting_data(meeting_id):
    pass

@meeting_bp.route("/api/summarize/<string:meeting_id>", methods=["POST"])
def summarize_meeting(meeting_id):
    pass

@meeting_bp.route("/api/generate_minutes/<string:meeting_id>", methods=["POST"])
def generate_minutes(meeting_id):
    pass

@meeting_bp.route("/api/delete_meeting/<string:meeting_id>", methods=["POST"])
def delete_meeting(meeting_id):
    pass
```

```python
# blueprints/chat.py
from flask import Blueprint

chat_bp = Blueprint('chat', __name__)

@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    pass
```

```python
# blueprints/share.py
from flask import Blueprint

share_bp = Blueprint('share', __name__)

@share_bp.route("/api/share/<string:meeting_id>", methods=["POST"])
def share_meeting_api(meeting_id):
    pass

@share_bp.route("/api/shared_users/<string:meeting_id>")
def get_shared_users_api(meeting_id):
    pass

@share_bp.route("/api/unshare/<string:meeting_id>/<int:user_id>", methods=["POST"])
def unshare_meeting_api(meeting_id, user_id):
    pass
```

```python
# blueprints/admin.py
from flask import Blueprint
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/retriever")
@admin_required
def retriever_page():
    pass

@admin_bp.route("/script-input")
@admin_required
def script_input_page():
    pass

@admin_bp.route("/summary_template")
@admin_required
def summary_template_page():
    pass
```

```python
# app.py (리팩토링 후 - 훨씬 간결해짐)
from flask import Flask
from blueprints.auth import auth_bp
from blueprints.upload import upload_bp
from blueprints.meeting import meeting_bp
from blueprints.chat import chat_bp
from blueprints.share import share_bp
from blueprints.admin import admin_bp

app = Flask(__name__)

# Blueprint 등록
app.register_blueprint(auth_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(meeting_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(share_bp)
app.register_blueprint(admin_bp)

# 메인 페이지만 여기에
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/notes")
@login_required
def list_notes():
    return render_template("notes.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
```

**예상 작업 시간**: 2-3시간
**효과**: 코드 가독성 3배 향상, 팀 협업 용이

---

### 2. 비즈니스 로직이 라우트에 섞여 있음 🔴 High Priority

**현재 문제 (app.py:357-510)**:
```python
@app.route("/upload", methods=["POST"])
def upload_and_process():
    # 1. 검증 로직 (20줄)
    title = request.form.get('title', '').strip()
    is_valid, error_message = validate_title(title)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    # 2. 파일 저장 로직 (10줄)
    filename = secure_filename(file.filename)
    file.save(original_file_path)

    # 3. 비디오 변환 로직 (20줄)
    if is_video:
        convert_video_to_audio(...)

    # 4. STT 처리 (10줄)
    segments = stt_manager.transcribe_audio(audio_path)

    # 5. DB 저장 (10줄)
    meeting_id = db.save_stt_to_db(segments, ...)

    # 6. Vector DB 저장 (30줄)
    vdb_manager.add_meeting_as_chunk(...)

    # 7. 요약 생성 (30줄)
    summary_content = stt_manager.subtopic_generate(...)

    # 8. 응답 처리 (10줄)
    return jsonify({"meeting_id": meeting_id})

    # 총 140줄이 한 함수에!
```

**개선 방안**: Service Layer 패턴 적용

```python
# services/upload_service.py
import os
from typing import Tuple, Optional
from werkzeug.utils import secure_filename
from utils.stt import STTManager
from utils.db_manager import DatabaseManager
from utils.vector_db_manager import vdb_manager

class UploadService:
    def __init__(self, upload_folder: str, db_path: str):
        self.upload_folder = upload_folder
        self.db = DatabaseManager(db_path)
        self.stt = STTManager()

    def process_audio_upload(
        self,
        file,
        title: str,
        user_id: int,
        meeting_date: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        오디오/비디오 파일 업로드를 처리합니다.

        Returns:
            (meeting_id, error_message)
        """
        try:
            # 1. 파일 저장
            file_path = self._save_uploaded_file(file)

            # 2. 비디오 → 오디오 변환 (필요시)
            audio_path = self._convert_if_video(file_path)

            # 3. STT 처리
            segments = self._transcribe(audio_path)
            if not segments:
                return None, "음성 인식에 실패했습니다"

            # 4. DB 저장
            meeting_id = self._save_to_database(
                segments, file.filename, title, meeting_date, user_id
            )

            # 5. 임시 파일 정리
            self._cleanup_temp_files(file_path, audio_path)

            # 6. 후처리 (Vector DB, 요약 생성)
            self._post_process(meeting_id)

            return meeting_id, None

        except Exception as e:
            return None, f"업로드 처리 중 오류: {str(e)}"

    def _save_uploaded_file(self, file) -> str:
        """업로드된 파일을 저장합니다."""
        filename = secure_filename(file.filename)
        file_path = os.path.join(self.upload_folder, filename)
        file.save(file_path)
        return file_path

    def _convert_if_video(self, file_path: str) -> str:
        """MP4 파일이면 WAV로 변환합니다."""
        if file_path.endswith('.mp4'):
            audio_path = file_path.replace('.mp4', '_audio.wav')
            success = self._convert_video_to_audio(file_path, audio_path)
            if not success:
                raise Exception("비디오 변환 실패")
            return audio_path
        return file_path

    def _convert_video_to_audio(self, video_path: str, audio_path: str) -> bool:
        """ffmpeg로 비디오를 오디오로 변환합니다."""
        import subprocess
        command = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1', audio_path
        ]
        try:
            result = subprocess.run(command, capture_output=True, timeout=300)
            return result.returncode == 0
        except:
            return False

    def _transcribe(self, audio_path: str):
        """Gemini로 음성 인식을 수행합니다."""
        return self.stt.transcribe_audio(audio_path)

    def _save_to_database(
        self,
        segments,
        filename: str,
        title: str,
        meeting_date: str,
        user_id: int
    ) -> str:
        """SQLite DB에 저장합니다."""
        return self.db.save_stt_to_db(
            segments, filename, title, meeting_date, user_id
        )

    def _cleanup_temp_files(self, original_path: str, audio_path: str):
        """임시 WAV 파일을 삭제합니다."""
        if audio_path != original_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass

    def _post_process(self, meeting_id: str):
        """Vector DB 저장 및 요약 생성을 수행합니다."""
        # Vector DB 저장
        all_segments = self.db.get_segments_by_meeting_id(meeting_id)
        if all_segments:
            first_segment = all_segments[0]
            vdb_manager.add_meeting_as_chunk(
                meeting_id=meeting_id,
                title=first_segment['title'],
                meeting_date=first_segment['meeting_date'],
                audio_file=first_segment['audio_file'],
                segments=all_segments
            )

            # 문단 요약 생성
            transcript_text = " ".join([row['segment'] for row in all_segments])
            summary_content = self.stt.subtopic_generate(
                first_segment['title'],
                transcript_text
            )

            if summary_content:
                vdb_manager.add_meeting_as_subtopic(
                    meeting_id=meeting_id,
                    title=first_segment['title'],
                    meeting_date=first_segment['meeting_date'],
                    audio_file=first_segment['audio_file'],
                    summary_content=summary_content
                )
```

```python
# blueprints/upload.py (리팩토링 후)
from flask import Blueprint, request, jsonify, redirect, url_for, session
from services.upload_service import UploadService
from utils.validation import validate_title
from utils.decorators import login_required

upload_bp = Blueprint('upload', __name__)
upload_service = UploadService(
    upload_folder="uploads",
    db_path="database/minute_ai.db"
)

@upload_bp.route("/upload", methods=["POST"])
@login_required
def upload_and_process():
    """오디오/비디오 파일 업로드 및 처리"""
    # 1. 입력 검증
    title = request.form.get('title', '').strip()
    is_valid, error_message = validate_title(title)
    if not is_valid:
        return jsonify({"success": False, "error": error_message}), 400

    if 'audio_file' not in request.files:
        return jsonify({"success": False, "error": "파일이 없습니다"}), 400

    file = request.files['audio_file']
    if not file.filename:
        return jsonify({"success": False, "error": "파일명이 없습니다"}), 400

    # 2. Service Layer로 처리 위임
    user_id = session['user_id']
    meeting_id, error = upload_service.process_audio_upload(
        file=file,
        title=title,
        user_id=user_id
    )

    # 3. 결과 반환
    if error:
        return jsonify({"success": False, "error": error}), 500

    return jsonify({
        "success": True,
        "meeting_id": meeting_id,
        "redirect_url": url_for('meeting.view_meeting', meeting_id=meeting_id)
    })
```

**예상 작업 시간**: 4-5시간
**효과**:
- 라우트가 10줄로 줄어듦 (140줄 → 10줄)
- 비즈니스 로직 테스트 가능
- 코드 재사용성 향상

---

### 3. 에러 처리가 너무 광범위함 🟡 Medium Priority

**현재 문제**:
```python
try:
    # 100줄의 코드
    # - 파일 검증
    # - DB 저장
    # - API 호출
except Exception as e:  # 모든 에러를 똑같이 처리
    return jsonify({"error": f"서버 처리 중 오류: {e}"}), 500
```

**문제점**:
- 어떤 단계에서 오류가 발생했는지 알 수 없음
- 사용자에게 구체적인 에러 메시지를 줄 수 없음
- 로깅/모니터링 어려움

**개선 방안**: 커스텀 Exception 클래스

```python
# exceptions.py
class MinuteAIException(Exception):
    """Base exception for Minute AI"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class FileValidationError(MinuteAIException):
    """파일 검증 오류"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class STTProcessingError(MinuteAIException):
    """STT 처리 오류"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

class DatabaseError(MinuteAIException):
    """데이터베이스 오류"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

class UnauthorizedError(MinuteAIException):
    """권한 없음"""
    def __init__(self, message: str = "접근 권한이 없습니다"):
        super().__init__(message, status_code=403)

class NotFoundError(MinuteAIException):
    """리소스 없음"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)
```

```python
# services/upload_service.py (개선)
from exceptions import FileValidationError, STTProcessingError, DatabaseError

class UploadService:
    def process_audio_upload(self, file, title: str, user_id: int):
        # 파일 검증
        if not self._is_allowed_file(file.filename):
            raise FileValidationError(
                f"허용되지 않는 파일 형식입니다. "
                f"지원 형식: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # STT 처리
        segments = self._transcribe(audio_path)
        if not segments:
            raise STTProcessingError(
                "음성 인식에 실패했습니다. API 키를 확인해주세요."
            )

        # DB 저장
        try:
            meeting_id = self.db.save_stt_to_db(segments, ...)
        except Exception as e:
            raise DatabaseError(f"DB 저장 실패: {str(e)}")

        return meeting_id
```

```python
# blueprints/upload.py (개선)
from exceptions import (
    FileValidationError,
    STTProcessingError,
    DatabaseError,
    MinuteAIException
)
import logging

logger = logging.getLogger(__name__)

@upload_bp.route("/upload", methods=["POST"])
@login_required
def upload_and_process():
    try:
        meeting_id = upload_service.process_audio_upload(...)
        return jsonify({"success": True, "meeting_id": meeting_id})

    except FileValidationError as e:
        # 사용자 입력 오류 - 400
        logger.warning(f"파일 검증 실패: {e.message}")
        return jsonify({"success": False, "error": e.message}), e.status_code

    except STTProcessingError as e:
        # STT 서비스 오류 - 500
        logger.error(f"STT 처리 실패: {e.message}")
        return jsonify({"success": False, "error": e.message}), e.status_code

    except DatabaseError as e:
        # DB 오류 - 500
        logger.error(f"DB 오류: {e.message}")
        return jsonify({"success": False, "error": "데이터 저장 실패"}), e.status_code

    except MinuteAIException as e:
        # 기타 정의된 오류
        logger.error(f"애플리케이션 오류: {e.message}")
        return jsonify({"success": False, "error": e.message}), e.status_code

    except Exception as e:
        # 예상치 못한 오류
        logger.exception(f"예상치 못한 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": "서버 내부 오류가 발생했습니다"
        }), 500
```

```python
# app.py에 전역 에러 핸들러 추가
from exceptions import MinuteAIException

@app.errorhandler(MinuteAIException)
def handle_minute_ai_exception(error):
    """모든 MinuteAI 커스텀 예외를 처리"""
    return jsonify({
        "success": False,
        "error": error.message
    }), error.status_code

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "페이지를 찾을 수 없습니다"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.exception("서버 내부 오류")
    return jsonify({
        "success": False,
        "error": "서버 내부 오류가 발생했습니다"
    }), 500
```

**예상 작업 시간**: 2-3시간
**효과**:
- 에러 원인 파악 용이
- 사용자에게 명확한 피드백
- 로깅/모니터링 가능

---

### 4. 하드코딩된 값들 🔴 High Priority

**현재 문제**:
```python
# utils/user_manager.py:12
ADMIN_EMAILS = ["admin@example.com"]  # 하드코딩

# app.py:55
ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "flac", "mp4"}

# app.py:104
timeout=300  # 왜 300초?

# static/css/style.css
background: #3498db;  # 색상 하드코딩
```

**개선 방안**: Config 클래스로 중앙화

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """애플리케이션 설정"""

    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    DEBUG = os.getenv("FLASK_DEBUG", "False") == "True"
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", "5050"))

    # Database
    DB_PATH = os.path.join(os.path.dirname(__file__), "database", "minute_ai.db")

    # Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "flac", "mp4"}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    # Video Processing
    VIDEO_CONVERSION_TIMEOUT = 300  # 5분
    FFMPEG_SAMPLE_RATE = 16000  # Hz
    FFMPEG_CHANNELS = 1  # 모노

    # STT
    STT_MODEL = "gemini-2.5-pro"
    MAX_SENTENCES_PER_SEGMENT = 5

    # LLM
    SUMMARY_MODEL = "gemini-2.5-pro"
    MINUTES_MODEL = "gemini-2.5-pro"
    CHAT_MODEL = "gemini-2.5-flash"

    # Vector DB
    EMBEDDING_MODEL = "text-embedding-3-small"
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    # Admin
    ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",")

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # Firebase
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
    FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
    FIREBASE_MESSAGING_SENDER_ID = os.getenv("FIREBASE_MESSAGING_SENDER_ID")
    FIREBASE_APP_ID = os.getenv("FIREBASE_APP_ID")
    FIREBASE_MEASUREMENT_ID = os.getenv("FIREBASE_MEASUREMENT_ID")

    # Theme (UI)
    PRIMARY_COLOR = "#3498db"
    SECONDARY_COLOR = "#2980b9"
    BACKGROUND_COLOR = "#f8f9fa"
    MENU_COLOR = "#2c3e50"

    @classmethod
    def validate(cls):
        """필수 설정 검증"""
        required = [
            "SECRET_KEY",
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY",
            "FIREBASE_API_KEY"
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing)}")


class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True


class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    DEBUG = False
    # 프로덕션에서는 PostgreSQL 사용
    # DB_URL = os.getenv("DATABASE_URL")


# 환경에 따라 설정 선택
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

```python
# app.py (개선)
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 설정 검증
Config.validate()

# 설정 사용
app.config["UPLOAD_FOLDER"] = Config.UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_FILE_SIZE
```

```python
# utils/stt.py (개선)
from config import Config

class STTManager:
    def transcribe_audio(self, audio_path):
        response = client.models.generate_content(
            model=Config.STT_MODEL,  # "gemini-2.5-pro"
            contents=[prompt, audio_data]
        )
```

```python
# .env에 추가
ADMIN_EMAILS=admin@example.com,user2@example.com
FLASK_DEBUG=True
FLASK_PORT=5050
```

**예상 작업 시간**: 1시간
**효과**:
- 설정 변경이 한 곳에서 가능
- 환경별 설정 분리 가능
- 필수 설정 누락 방지

---

### 5. 동기 처리로 인한 블로킹 🟡 Medium Priority

**현재 문제**:
```python
@app.route("/upload", methods=["POST"])
def upload():
    # STT 처리 - 5분 동안 블로킹!
    segments = stt_manager.transcribe_audio(file)

    # 사용자는 5분간 응답 대기...
    # 브라우저 타임아웃 가능
```

**개선 방안**: Celery로 비동기 처리

```python
# celery_app.py
from celery import Celery
from config import Config

celery = Celery(
    'minute_ai',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
)
```

```python
# tasks/processing.py
from celery_app import celery
from services.upload_service import upload_service
import logging

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3)
def process_audio_async(self, meeting_id: str, file_path: str, title: str, user_id: int):
    """
    오디오 파일을 비동기로 처리합니다.

    Args:
        meeting_id: 회의 ID (미리 생성됨)
        file_path: 저장된 파일 경로
        title: 회의 제목
        user_id: 사용자 ID
    """
    try:
        # 진행 상황 업데이트
        self.update_state(state='PROCESSING', meta={'progress': 0, 'status': 'STT 시작'})

        # STT 처리
        segments = upload_service._transcribe(file_path)
        self.update_state(state='PROCESSING', meta={'progress': 40, 'status': 'STT 완료'})

        # DB 저장
        upload_service._save_to_database(segments, file_path, title, None, user_id)
        self.update_state(state='PROCESSING', meta={'progress': 60, 'status': 'DB 저장 완료'})

        # Vector DB 저장
        upload_service._post_process(meeting_id)
        self.update_state(state='PROCESSING', meta={'progress': 100, 'status': '완료'})

        return {
            'meeting_id': meeting_id,
            'status': 'completed'
        }

    except Exception as e:
        logger.error(f"비동기 처리 실패: {e}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
```

```python
# blueprints/upload.py (비동기 버전)
from tasks.processing import process_audio_async
import uuid

@upload_bp.route("/upload", methods=["POST"])
@login_required
def upload_and_process():
    # 1. 입력 검증
    # ... (동일)

    # 2. 파일만 먼저 저장
    filename = secure_filename(file.filename)
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(file_path)

    # 3. meeting_id 미리 생성
    meeting_id = str(uuid.uuid4())

    # 4. 비동기 작업 시작
    task = process_audio_async.delay(
        meeting_id=meeting_id,
        file_path=file_path,
        title=title,
        user_id=session['user_id']
    )

    # 5. 즉시 응답 반환
    return jsonify({
        "success": True,
        "meeting_id": meeting_id,
        "task_id": task.id,
        "status": "processing",
        "message": "업로드가 시작되었습니다. 처리 중입니다..."
    })


@upload_bp.route("/api/task/<task_id>")
@login_required
def get_task_status(task_id):
    """비동기 작업 진행 상황 조회"""
    task = process_audio_async.AsyncResult(task_id)

    if task.state == 'PENDING':
        response = {'state': task.state, 'progress': 0}
    elif task.state == 'PROCESSING':
        response = {
            'state': task.state,
            'progress': task.info.get('progress', 0),
            'status': task.info.get('status', '')
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'progress': 100,
            'meeting_id': task.info.get('meeting_id')
        }
    else:  # FAILURE
        response = {
            'state': task.state,
            'error': str(task.info)
        }

    return jsonify(response)
```

```javascript
// static/js/upload.js (프론트엔드)
async function uploadFile(file, title) {
    // 1. 업로드 시작
    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();
    const taskId = data.task_id;

    // 2. 진행 상황 폴링
    const checkProgress = setInterval(async () => {
        const statusResponse = await fetch(`/api/task/${taskId}`);
        const status = await statusResponse.json();

        // 프로그레스바 업데이트
        updateProgressBar(status.progress);
        updateStatusText(status.status);

        if (status.state === 'SUCCESS') {
            clearInterval(checkProgress);
            // 완료 페이지로 이동
            window.location.href = `/view/${status.meeting_id}`;
        } else if (status.state === 'FAILURE') {
            clearInterval(checkProgress);
            showError(status.error);
        }
    }, 2000);  // 2초마다 확인
}
```

**추가 설치 필요**:
```bash
pip install celery redis
# Redis 서버 실행 필요
```

**실행 방법**:
```bash
# Terminal 1: Flask 서버
python app.py

# Terminal 2: Celery Worker
celery -A celery_app worker --loglevel=info

# Terminal 3: Redis (Docker)
docker run -d -p 6379:6379 redis
```

**예상 작업 시간**: 1일
**효과**:
- 사용자 경험 개선 (즉시 응답)
- 서버 부하 분산
- 처리 실패 시 재시도 가능

---

### 6. 테스트 코드 부재 🟢 Low Priority

**현재 문제**: 테스트 파일이 전혀 없음

**개선 방안**: pytest 도입

```python
# tests/conftest.py
import pytest
from app import app
from config import Config

@pytest.fixture
def client():
    """Flask 테스트 클라이언트"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_client(client):
    """인증된 클라이언트"""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['email'] = 'test@example.com'
    return client
```

```python
# tests/test_stt.py
import pytest
from utils.stt import STTManager

def test_transcribe_audio():
    """음성 인식 테스트"""
    stt = STTManager()
    segments = stt.transcribe_audio("tests/fixtures/test_audio.wav")

    assert segments is not None
    assert len(segments) > 0
    assert 'speaker' in segments[0]
    assert 'text' in segments[0]
    assert 'confidence' in segments[0]

def test_parse_script():
    """스크립트 파싱 테스트"""
    stt = STTManager()
    script = """
    화자1: 안녕하세요
    화자2: 반갑습니다
    """
    segments = stt.parse_script(script)

    assert len(segments) == 2
    assert segments[0]['speaker'] == 1
    assert segments[1]['speaker'] == 2
```

```python
# tests/test_upload.py
import pytest
from io import BytesIO

def test_upload_without_auth(client):
    """인증 없이 업로드 시 401 반환"""
    response = client.post('/upload')
    assert response.status_code == 302  # 로그인 페이지로 리다이렉트

def test_upload_with_valid_file(auth_client):
    """정상 파일 업로드"""
    data = {
        'title': '테스트 회의',
        'audio_file': (BytesIO(b'fake audio data'), 'test.wav')
    }
    response = auth_client.post('/upload', data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] == True
    assert 'meeting_id' in json_data

def test_upload_without_title(auth_client):
    """제목 없이 업로드 시 400 반환"""
    data = {
        'audio_file': (BytesIO(b'fake audio data'), 'test.wav')
    }
    response = auth_client.post('/upload', data=data, content_type='multipart/form-data')

    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] == False
```

```python
# tests/test_db_manager.py
import pytest
from utils.db_manager import DatabaseManager
import tempfile
import os

@pytest.fixture
def temp_db():
    """임시 DB 생성"""
    fd, path = tempfile.mkstemp(suffix='.db')
    db = DatabaseManager(path)
    yield db
    os.close(fd)
    os.unlink(path)

def test_save_and_get_meeting(temp_db):
    """회의 저장 및 조회"""
    segments = [
        {'speaker': 1, 'start_time': 0.0, 'text': '안녕하세요', 'confidence': 0.95}
    ]

    meeting_id = temp_db.save_stt_to_db(
        segments, 'test.wav', '테스트 회의', owner_id=1
    )

    rows = temp_db.get_meeting_by_id(meeting_id)
    assert len(rows) == 1
    assert rows[0]['title'] == '테스트 회의'
```

```python
# tests/test_user_manager.py
import pytest
from utils.user_manager import get_or_create_user, can_access_meeting

def test_create_user():
    """사용자 생성"""
    user = get_or_create_user(
        google_id='test123',
        email='test@example.com',
        name='테스트'
    )

    assert user['email'] == 'test@example.com'
    assert user['role'] == 'user'

def test_admin_user():
    """관리자 체크"""
    # config.py에서 ADMIN_EMAILS 설정 필요
    from utils.user_manager import is_admin

    admin_user = get_or_create_user(
        google_id='admin123',
        email='admin@example.com'
    )

    assert is_admin(admin_user['id']) == True
```

**실행 방법**:
```bash
# 테스트 실행
pytest

# 커버리지 확인
pytest --cov=utils --cov=services

# 특정 테스트만 실행
pytest tests/test_stt.py
```

**예상 작업 시간**: 2-3일
**효과**:
- 버그 조기 발견
- 리팩토링 시 안전성 확보
- 코드 품질 향상

---

### 7. 타입 힌트 부족 🟡 Medium Priority

**현재 문제**:
```python
def save_stt_to_db(self, segments, audio_filename, title, meeting_date=None, owner_id=None):
    # 타입이 명확하지 않음
    # segments가 무엇인지?
    # 반환값은?
```

**개선 방안**: Type Hints 추가

```python
# utils/db_manager.py (개선)
from typing import List, Dict, Optional, Any
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def save_stt_to_db(
        self,
        segments: List[Dict[str, Any]],
        audio_filename: str,
        title: str,
        meeting_date: Optional[str] = None,
        owner_id: Optional[int] = None
    ) -> str:
        """
        음성 인식 결과를 데이터베이스에 저장합니다.

        Args:
            segments: 음성 인식 결과 세그먼트 리스트
                [{
                    'speaker': int,
                    'start_time': float,
                    'text': str,
                    'confidence': float
                }, ...]
            audio_filename: 오디오 파일명
            title: 회의 제목
            meeting_date: 회의 일시 (형식: "YYYY-MM-DD HH:MM:SS")
            owner_id: 회의 소유자 ID

        Returns:
            생성된 meeting_id (UUID 문자열)
        """
        # 구현...
        return meeting_id

    def get_meeting_by_id(self, meeting_id: str) -> List[Dict[str, Any]]:
        """
        meeting_id로 회의 데이터를 조회합니다.

        Returns:
            회의 세그먼트 리스트
        """
        # 구현...
        return rows
```

```python
# services/upload_service.py (개선)
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage

class UploadService:
    def process_audio_upload(
        self,
        file: FileStorage,
        title: str,
        user_id: int,
        meeting_date: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        오디오/비디오 파일 업로드를 처리합니다.

        Args:
            file: 업로드된 파일 객체
            title: 회의 제목
            user_id: 사용자 ID
            meeting_date: 회의 일시 (선택)

        Returns:
            (meeting_id, error_message) 튜플
            - 성공: (meeting_id, None)
            - 실패: (None, error_message)
        """
        # 구현...
```

**VS Code 설정** (`.vscode/settings.json`):
```json
{
    "python.linting.mypyEnabled": true,
    "python.linting.enabled": true
}
```

**타입 체크 실행**:
```bash
# mypy 설치
pip install mypy

# 타입 체크
mypy utils/ services/
```

**예상 작업 시간**: 2-3시간
**효과**:
- IDE 자동완성 향상
- 타입 오류 조기 발견
- 코드 가독성 향상

---

### 8. 로깅 시스템 부족 🟢 Low Priority

**현재 문제**:
```python
print(f"✅ DB 저장 완료")  # print 문으로 로깅
```

**개선 방안**: Python logging 모듈 사용

```python
# logging_config.py
import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(app):
    """애플리케이션 로깅 설정"""

    # 로그 디렉토리 생성
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 로그 포맷
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # 파일 핸들러 (일별 로테이션)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'minute_ai.log'),
        when='midnight',
        interval=1,
        backupCount=30,  # 30일 보관
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # 에러 로그 별도 파일
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'errors.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    # 콘솔 핸들러 (개발 환경)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # Flask 앱 로거 설정
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # 다른 모듈 로거도 설정
    logging.getLogger('werkzeug').addHandler(file_handler)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
```

```python
# app.py (개선)
from logging_config import setup_logging
import logging

app = Flask(__name__)
setup_logging(app)
logger = logging.getLogger(__name__)

@app.route("/upload", methods=["POST"])
def upload():
    logger.info(f"업로드 요청 수신: user_id={session['user_id']}")

    try:
        meeting_id = upload_service.process_audio_upload(...)
        logger.info(f"업로드 성공: meeting_id={meeting_id}")
        return jsonify({"meeting_id": meeting_id})

    except Exception as e:
        logger.error(f"업로드 실패: {str(e)}", exc_info=True)
        return jsonify({"error": "업로드 실패"}), 500
```

```python
# utils/db_manager.py (개선)
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def save_stt_to_db(self, segments, ...):
        logger.info(f"DB 저장 시작: title={title}, owner_id={owner_id}")

        # 저장 로직...

        logger.info(f"DB 저장 완료: meeting_id={meeting_id}, segments={len(segments)}개")
        return meeting_id
```

**로그 레벨**:
```python
logger.debug("디버깅 정보")      # 개발 중에만
logger.info("일반 정보")         # 중요한 이벤트
logger.warning("경고")           # 주의가 필요한 상황
logger.error("오류")             # 에러 발생
logger.critical("심각한 오류")   # 시스템 장애
```

**예상 작업 시간**: 1-2시간
**효과**:
- 프로덕션 디버깅 가능
- 사용 패턴 분석
- 오류 추적 용이

---

### 9. Magic Number 제거 🟢 Low Priority

**현재 문제**:
```python
# utils/stt.py:68
"단, 문장이 5개를 넘어갈 경우..."  # 왜 5개?

# app.py:104
timeout=300  # 왜 300초?

# utils/chat_manager.py
k=3  # 왜 3개?
```

**개선 방안**: constants.py로 분리

```python
# constants.py
"""애플리케이션 전역 상수"""

# STT 설정
MAX_SENTENCES_PER_SEGMENT = 5  # 한 세그먼트당 최대 문장 수
STT_CONFIDENCE_THRESHOLD = 0.8  # 최소 신뢰도

# 비디오 처리
VIDEO_CONVERSION_TIMEOUT = 300  # 초 (5분)
VIDEO_MAX_DURATION = 3600  # 초 (1시간)

# 검색 설정
DEFAULT_SEARCH_RESULTS = 3  # 기본 검색 결과 수
MAX_SEARCH_RESULTS = 10  # 최대 검색 결과 수

# UI 크기
CHATBOT_TAB_WIDTH = 40  # px
CHATBOT_SIDEBAR_WIDTH = 400  # px

# 파일 크기 제한
MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB

# 캐시 설정
CACHE_TTL = 3600  # 초 (1시간)

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 2  # 초
```

```python
# utils/stt.py (개선)
from constants import MAX_SENTENCES_PER_SEGMENT

prompt = f"""
...
13. speaker가 동일한 경우 하나의 행으로 만듭니다.
    단, 문장이 {MAX_SENTENCES_PER_SEGMENT}개를 넘어갈 경우 다음 대화로 분리한다.
"""
```

```python
# services/upload_service.py (개선)
from constants import VIDEO_CONVERSION_TIMEOUT

def _convert_video_to_audio(self, video_path, audio_path):
    result = subprocess.run(
        command,
        capture_output=True,
        timeout=VIDEO_CONVERSION_TIMEOUT
    )
```

**예상 작업 시간**: 30분
**효과**:
- 값의 의미 명확화
- 수정 시 한 곳만 변경
- 일관성 유지

---

### 10. 동시성 처리 미비 🟡 Medium Priority

**현재 문제**:
- SQLite는 write lock 발생 가능
- 여러 사용자 동시 업로드 시 병목

**개선 방안 1**: PostgreSQL 전환

```python
# requirements.txt에 추가
psycopg2-binary==2.9.9
SQLAlchemy==2.0.23

# config.py
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/minute_ai"
)
```

```python
# models.py (SQLAlchemy ORM)
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    google_id = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    profile_picture = Column(String(512))
    role = Column(String(20), default='user')
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    meetings = relationship("MeetingDialogue", back_populates="owner")
    shared_meetings = relationship("MeetingShare", foreign_keys="MeetingShare.shared_with_id")


class MeetingDialogue(Base):
    __tablename__ = 'meeting_dialogues'

    id = Column(Integer, primary_key=True)
    meeting_id = Column(String(36), nullable=False, index=True)
    meeting_date = Column(DateTime, nullable=False)
    speaker_label = Column(String(50), nullable=False)
    start_time = Column(Float, nullable=False)
    segment = Column(Text, nullable=False)
    confidence = Column(Float)
    audio_file = Column(String(512), nullable=False)
    title = Column(String(512), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'))

    # Relationships
    owner = relationship("User", back_populates="meetings")


class MeetingMinute(Base):
    __tablename__ = 'meeting_minutes'

    meeting_id = Column(String(36), primary_key=True)
    title = Column(String(512), nullable=False)
    meeting_date = Column(DateTime, nullable=False)
    minutes_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'))
```

**개선 방안 2**: Redis 큐 도입

```python
# services/queue_service.py
import redis
import json

class QueueService:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0)

    def enqueue_upload(self, job_data: dict) -> str:
        """업로드 작업을 큐에 추가"""
        job_id = str(uuid.uuid4())
        self.redis.lpush('upload_queue', json.dumps({
            'job_id': job_id,
            **job_data
        }))
        return job_id

    def get_job_status(self, job_id: str) -> dict:
        """작업 상태 조회"""
        status = self.redis.get(f'job:{job_id}:status')
        if status:
            return json.loads(status)
        return {'state': 'PENDING'}
```

**예상 작업 시간**: 1일
**효과**:
- 동시 사용자 처리 가능
- 데이터 무결성 보장
- 확장성 확보

---

## 🎯 리팩토링 우선순위 및 로드맵

### 🔴 Phase 1: 기초 인프라 (1주)

**목표**: 코드 구조 개선

1. **Config 클래스 추가** (1시간)
   - `config.py` 생성
   - 하드코딩된 값 제거
   - 환경별 설정 분리

2. **Constants 정의** (30분)
   - `constants.py` 생성
   - Magic Number 제거

3. **Custom Exception 클래스** (2시간)
   - `exceptions.py` 생성
   - 에러 타입 정의
   - 전역 에러 핸들러

4. **Blueprint 분리** (3시간)
   - `blueprints/` 디렉토리 생성
   - 라우트를 카테고리별로 분리
   - app.py 슬림화

**검증**:
- [ ] app.py가 200줄 이하로 줄어듦
- [ ] 모든 설정이 config.py에 있음
- [ ] 에러 메시지가 구체적으로 표시됨

---

### 🟡 Phase 2: 서비스 레이어 (1주)

**목표**: 비즈니스 로직 분리

5. **Service Layer 추가** (1일)
   - `services/upload_service.py`
   - `services/meeting_service.py`
   - `services/chat_service.py`

6. **타입 힌트 추가** (3시간)
   - 모든 함수에 타입 힌트
   - docstring 작성
   - mypy 검증

7. **로깅 시스템** (2시간)
   - `logging_config.py` 생성
   - 파일 로깅 설정
   - 로그 레벨 정의

**검증**:
- [ ] 라우트 함수가 20줄 이하
- [ ] 비즈니스 로직이 테스트 가능
- [ ] 로그 파일이 생성됨

---

### 🟢 Phase 3: 성능 & 테스트 (2주)

**목표**: 안정성 및 확장성 확보

8. **비동기 처리** (2일)
   - Celery + Redis 설치
   - 비동기 작업 정의
   - 진행 상황 API

9. **테스트 코드** (3일)
   - pytest 설정
   - 단위 테스트 작성
   - 통합 테스트 작성

10. **데이터베이스 마이그레이션** (2일)
    - PostgreSQL 전환 (선택)
    - 또는 SQLite 최적화

**검증**:
- [ ] 업로드 시 즉시 응답
- [ ] 테스트 커버리지 70% 이상
- [ ] 동시 사용자 10명 처리 가능

---

## 📋 리팩토링 체크리스트

### Before Starting
- [ ] Git branch 생성 (`feature/refactoring`)
- [ ] 현재 코드 백업
- [ ] 테스트 환경 준비

### Phase 1 (기초 인프라)
- [ ] config.py 생성 완료
- [ ] constants.py 생성 완료
- [ ] exceptions.py 생성 완료
- [ ] Blueprint 분리 완료
- [ ] 모든 라우트 정상 작동 확인

### Phase 2 (서비스 레이어)
- [ ] UploadService 구현 완료
- [ ] MeetingService 구현 완료
- [ ] ChatService 구현 완료
- [ ] 타입 힌트 추가 완료
- [ ] 로깅 시스템 적용 완료

### Phase 3 (성능 & 테스트)
- [ ] Celery 설정 완료
- [ ] 비동기 업로드 작동 확인
- [ ] 단위 테스트 70% 커버리지
- [ ] 통합 테스트 작성 완료
- [ ] PostgreSQL 마이그레이션 (선택)

### Final Check
- [ ] 모든 기능 정상 작동
- [ ] 성능 테스트 통과
- [ ] 문서 업데이트 (next.md)
- [ ] main branch 머지

---

## 💰 예상 비용

| Phase | 작업 시간 | 비용 (시급 5만원 기준) |
|-------|----------|-------------------|
| Phase 1 | 8시간 | 40만원 |
| Phase 2 | 40시간 | 200만원 |
| Phase 3 | 80시간 | 400만원 |
| **합계** | **128시간** | **640만원** |

---

## 🎓 학습 자료

### Flask Blueprint
- https://flask.palletsprojects.com/en/2.3.x/blueprints/

### Service Layer Pattern
- https://martinfowler.com/eaaCatalog/serviceLayer.html

### Python Type Hints
- https://docs.python.org/3/library/typing.html

### Celery Async Tasks
- https://docs.celeryq.dev/en/stable/

### pytest Testing
- https://docs.pytest.org/en/stable/

---

## 📞 질문 및 피드백

리팩토링 중 질문이나 막히는 부분이 있으면:
1. 이 문서의 예제 코드 참고
2. next.md의 기존 코드 패턴 참고
3. 공식 문서 확인

**Important**:
- 리팩토링은 한 번에 하지 말고 **Phase별로 진행**
- 각 Phase 완료 후 **Git commit**
- 기능이 정상 작동하는지 **매번 확인**

---

**작성자**: Claude Code
**최종 수정**: 2025-11-06
**버전**: 1.0
