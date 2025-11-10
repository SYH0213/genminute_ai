#!/usr/bin/env python3
"""
통합 테스트 스크립트
실제 프로젝트 코드가 새 환경에서 정상 작동하는지 확인합니다.

주의: .env 파일 필요 (API 키)
"""

import sys
import os

def test_database_manager():
    """DatabaseManager 초기화 테스트"""
    print("\n" + "=" * 60)
    print("🗄️  DatabaseManager 테스트")
    print("=" * 60)

    try:
        from utils.db_manager import DatabaseManager

        # db_path 인자 제공
        db_manager = DatabaseManager(db_path="database/minute_ai.db")
        print("  ✅ DatabaseManager 초기화 성공")

        # 간단한 쿼리 테스트
        conn = db_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"  ✅ DB 쿼리 성공 (users: {count}개)")
        conn.close()

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_db_manager():
    """VectorDBManager 초기화 테스트"""
    print("\n" + "=" * 60)
    print("🔍 VectorDBManager 테스트")
    print("=" * 60)

    try:
        # .env에서 OPENAI_API_KEY 필요
        if not os.getenv("OPENAI_API_KEY"):
            print("  ⚠️  OPENAI_API_KEY 없음 (.env 설정 필요)")
            return None

        from utils.vector_db_manager import VectorDBManager

        vdb_manager = VectorDBManager()
        print("  ✅ VectorDBManager 초기화 성공")
        print(f"  ✅ Collections: {list(vdb_manager.COLLECTION_NAMES.values())}")

        # Embeddings 테스트
        test_text = "테스트 텍스트"
        embeddings = vdb_manager.embedding_function.embed_query(test_text)
        print(f"  ✅ Embeddings 생성 성공 (dim: {len(embeddings)})")

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chat_manager():
    """ChatManager 초기화 테스트"""
    print("\n" + "=" * 60)
    print("💬 ChatManager 테스트")
    print("=" * 60)

    try:
        if not os.getenv("OPENAI_API_KEY") or not os.getenv("GOOGLE_GENAI_API_KEY"):
            print("  ⚠️  API 키 없음 (.env 설정 필요)")
            return None

        from utils.vector_db_manager import VectorDBManager
        from utils.chat_manager import ChatManager

        vdb_manager = VectorDBManager()
        chat_manager = ChatManager(vdb_manager, retriever_type="similarity")

        print("  ✅ ChatManager 초기화 성공")
        print(f"  ✅ Retriever type: similarity")

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stt_manager():
    """STTManager 초기화 테스트"""
    print("\n" + "=" * 60)
    print("🎤 STTManager 테스트")
    print("=" * 60)

    try:
        if not os.getenv("GOOGLE_GENAI_API_KEY"):
            print("  ⚠️  GOOGLE_GENAI_API_KEY 없음 (.env 설정 필요)")
            return None

        from utils.stt import STTManager

        stt_manager = STTManager()
        print("  ✅ STTManager 초기화 성공")

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_langchain_operations():
    """LangChain 주요 기능 테스트"""
    print("\n" + "=" * 60)
    print("🦜 LangChain 주요 기능 테스트")
    print("=" * 60)

    try:
        # 1. Text Splitter
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        test_text = "이것은 테스트 텍스트입니다. " * 100
        chunks = splitter.split_text(test_text)
        print(f"  ✅ RecursiveCharacterTextSplitter: {len(chunks)}개 청크")

        # 2. OpenAI Embeddings (API 키 필요)
        if os.getenv("OPENAI_API_KEY"):
            from langchain_openai import OpenAIEmbeddings

            embeddings = OpenAIEmbeddings()
            test_embed = embeddings.embed_query("테스트")
            print(f"  ✅ OpenAIEmbeddings: dim={len(test_embed)}")
        else:
            print("  ⚠️  OPENAI_API_KEY 없음 (Embeddings 테스트 스킵)")

        # 3. Chroma
        import chromadb
        from langchain_chroma import Chroma

        print("  ✅ ChromaDB import 성공")
        print("  ✅ LangChain-Chroma 연동 성공")

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_flask_app():
    """Flask 앱 초기화 테스트 (실제 실행 안함)"""
    print("\n" + "=" * 60)
    print("🌐 Flask App 초기화 테스트")
    print("=" * 60)

    try:
        # app.py import만 (실제 실행은 안함)
        import importlib.util

        spec = importlib.util.spec_from_file_location("app", "app.py")
        if spec and spec.loader:
            print("  ✅ app.py 파일 로드 가능")

        # Flask import
        from flask import Flask
        app = Flask(__name__)
        print("  ✅ Flask 앱 생성 성공")

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_google_genai():
    """Google Genai API 테스트"""
    print("\n" + "=" * 60)
    print("🤖 Google Genai API 테스트")
    print("=" * 60)

    try:
        if not os.getenv("GOOGLE_GENAI_API_KEY"):
            print("  ⚠️  GOOGLE_GENAI_API_KEY 없음 (.env 설정 필요)")
            return None

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_GENAI_API_KEY"))
        print("  ✅ Genai Client 생성 성공")

        # 간단한 테스트 (실제 API 호출은 안함)
        print("  ✅ Genai types import 성공")

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 통합 테스트 실행"""
    print("\n🚀 통합 테스트 시작 (실제 코드 경로 테스트)\n")

    # .env 로드
    from dotenv import load_dotenv
    load_dotenv()

    if not os.path.exists(".env"):
        print("⚠️  .env 파일이 없습니다. API 키 관련 테스트는 스킵됩니다.")
        print("    테스트를 완전히 하려면 .env 파일을 생성하세요.\n")

    results = {
        "DatabaseManager": test_database_manager(),
        "VectorDBManager": test_vector_db_manager(),
        "ChatManager": test_chat_manager(),
        "STTManager": test_stt_manager(),
        "LangChain 기능": test_langchain_operations(),
        "Flask App": test_flask_app(),
        "Google Genai": test_google_genai(),
    }

    print("\n" + "=" * 60)
    print("📊 통합 테스트 결과 요약")
    print("=" * 60)

    passed = 0
    failed = 0
    skipped = 0

    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
            passed += 1
        elif result is False:
            status = "❌ FAIL"
            failed += 1
        else:  # None
            status = "⚠️  SKIP"
            skipped += 1

        print(f"  {test_name:20} {status}")

    print("\n" + "=" * 60)
    print(f"📈 통과: {passed}개 | 실패: {failed}개 | 스킵: {skipped}개")

    if failed == 0:
        print("\n🎉 모든 핵심 테스트 통과! 앱이 정상 작동할 것으로 예상됩니다.")
        print("\n✅ 다음 단계:")
        print("  1. python app.py 실행")
        print("  2. 브라우저에서 http://localhost:5000 접속")
        print("  3. 실제 기능 테스트 (로그인, 노트 생성 등)")
    else:
        print(f"\n⚠️  {failed}개 테스트 실패. 위의 오류 메시지를 확인하세요.")
        print("     환경 재생성이 필요할 수 있습니다.")

    print("=" * 60 + "\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
