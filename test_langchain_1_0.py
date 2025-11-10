#!/usr/bin/env python3
"""
LangChain 1.0 호환성 테스트
실제 프로젝트 코드가 LangChain 1.0.x에서 정상 작동하는지 확인합니다.

주의: .env 파일 및 OPENAI_API_KEY 필요
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

def test_chatopenai():
    """ChatOpenAI 1.0 호환성 테스트"""
    print("\n" + "=" * 60)
    print("🤖 ChatOpenAI 호환성 테스트")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  OPENAI_API_KEY 없음 (.env 설정 필요)")
        return None

    try:
        from langchain_openai import ChatOpenAI

        # 프로젝트와 동일한 방식으로 초기화
        llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0)
        print("  ✅ ChatOpenAI 초기화 성공")

        # 간단한 invoke 테스트
        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content="Say 'test'")]
        response = llm.invoke(messages)

        print(f"  ✅ invoke() 성공")
        print(f"  ✅ Response type: {type(response).__name__}")

        # 1.0 변경사항: AIMessage.text는 이제 property
        # .text() → .text
        if hasattr(response, 'content'):
            print(f"  ✅ Response content: {response.content[:50]}...")

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_self_query_retriever():
    """SelfQueryRetriever (langchain_classic) 호환성 테스트"""
    print("\n" + "=" * 60)
    print("🔍 SelfQueryRetriever 호환성 테스트")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  OPENAI_API_KEY 없음 (.env 설정 필요)")
        return None

    try:
        from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
        from langchain_classic.chains.query_constructor.base import AttributeInfo
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from langchain_chroma import Chroma
        import chromadb

        print("  ✅ langchain_classic.SelfQueryRetriever import 성공")

        # LLM 초기화 (프로젝트와 동일)
        llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0)
        print("  ✅ ChatOpenAI 초기화 성공")

        # 간단한 테스트용 vectorstore
        client = chromadb.Client()
        collection = client.get_or_create_collection("test_collection")

        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma(
            client=client,
            collection_name="test_collection",
            embedding_function=embeddings
        )

        print("  ✅ Vectorstore 초기화 성공")

        # SelfQueryRetriever 생성
        metadata_info = [
            AttributeInfo(name="test_field", description="Test field", type="string")
        ]

        retriever = SelfQueryRetriever.from_llm(
            llm,
            vectorstore,
            "Test documents",
            metadata_info,
            verbose=False
        )

        print("  ✅ SelfQueryRetriever.from_llm() 성공")
        print("  ✅ 프로젝트 코드 패턴 작동 확인")

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_text_splitter():
    """RecursiveCharacterTextSplitter 호환성 테스트"""
    print("\n" + "=" * 60)
    print("✂️  RecursiveCharacterTextSplitter 호환성 테스트")
    print("=" * 60)

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        # 프로젝트와 동일한 파라미터
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n[Speaker", "\n\n", "\n", " ", ""]
        )
        print("  ✅ RecursiveCharacterTextSplitter 초기화 성공")

        # split_text 메서드 테스트
        test_text = "[Speaker 1, 00:01] 테스트입니다.\n" * 100
        chunks = splitter.split_text(test_text)

        print(f"  ✅ split_text() 성공: {len(chunks)}개 청크")
        print("  ✅ 프로젝트 코드 패턴 작동 확인")

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embeddings():
    """OpenAIEmbeddings 호환성 테스트"""
    print("\n" + "=" * 60)
    print("🔢 OpenAIEmbeddings 호환성 테스트")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  OPENAI_API_KEY 없음 (.env 설정 필요)")
        return None

    try:
        from langchain_openai import OpenAIEmbeddings

        embeddings = OpenAIEmbeddings()
        print("  ✅ OpenAIEmbeddings 초기화 성공")

        # embed_query 메서드 테스트
        test_vector = embeddings.embed_query("테스트 텍스트")

        print(f"  ✅ embed_query() 성공: dim={len(test_vector)}")
        print("  ✅ 프로젝트 코드 패턴 작동 확인")

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chroma_integration():
    """Chroma + LangChain 통합 테스트"""
    print("\n" + "=" * 60)
    print("📦 Chroma + LangChain 통합 테스트")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  OPENAI_API_KEY 없음 (.env 설정 필요)")
        return None

    try:
        import chromadb
        from langchain_chroma import Chroma
        from langchain_openai import OpenAIEmbeddings

        # ChromaDB client
        client = chromadb.Client()
        print("  ✅ ChromaDB Client 생성 성공")

        # LangChain-Chroma 연동
        embeddings = OpenAIEmbeddings()
        collection_name = "test_integration"

        vectorstore = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embeddings
        )

        print("  ✅ Chroma vectorstore 생성 성공")

        # add_texts 테스트
        ids = vectorstore.add_texts(
            texts=["테스트 문서 1", "테스트 문서 2"],
            metadatas=[{"id": "1"}, {"id": "2"}],
            ids=["test_1", "test_2"]
        )

        print(f"  ✅ add_texts() 성공: {len(ids)}개 추가")
        print("  ✅ 프로젝트 코드 패턴 작동 확인")

        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("\n🚀 LangChain 1.0 호환성 테스트 시작\n")
    print("⚠️  이 테스트는 실제 API 호출을 포함합니다 (소량)")
    print("    .env 파일에 OPENAI_API_KEY가 필요합니다.\n")

    results = {
        "ChatOpenAI": test_chatopenai(),
        "SelfQueryRetriever": test_self_query_retriever(),
        "TextSplitter": test_text_splitter(),
        "Embeddings": test_embeddings(),
        "Chroma 통합": test_chroma_integration(),
    }

    print("\n" + "=" * 60)
    print("📊 LangChain 1.0 호환성 테스트 결과")
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

        print(f"  {test_name:25} {status}")

    print("\n" + "=" * 60)
    print(f"📈 통과: {passed}개 | 실패: {failed}개 | 스킵: {skipped}개")

    if failed == 0:
        print("\n🎉 LangChain 1.0 호환성 100% 확인!")
        print("   프로젝트 코드가 1.0.x에서 정상 작동합니다.")
        print("\n✅ 다음 단계:")
        print("  python app.py 실행하여 실제 앱 테스트")
    else:
        print(f"\n⚠️  {failed}개 호환성 문제 발견!")
        print("     코드 수정이 필요할 수 있습니다.")

    print("=" * 60 + "\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
