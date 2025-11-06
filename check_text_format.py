#!/usr/bin/env python3
"""
ChromaDB에 저장된 실제 텍스트 형식 확인 스크립트
"""
import chromadb
import os

# ChromaDB 연결
db_path = os.path.join(os.path.dirname(__file__), 'database', 'vector_db')
client = chromadb.PersistentClient(path=db_path)

try:
    # meeting_chunks 컬렉션에서 샘플 데이터 가져오기
    collection = client.get_collection(name='meeting_chunks')

    # 최대 3개의 문서 샘플 가져오기
    results = collection.get(
        limit=3,
        include=["documents", "metadatas"]
    )

    if results and results.get('documents'):
        print("=" * 80)
        print("📊 ChromaDB에 저장된 실제 텍스트 샘플")
        print("=" * 80)

        for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas']), 1):
            print(f"\n[샘플 {i}]")
            print(f"Meeting ID: {meta.get('meeting_id', 'N/A')}")
            print(f"Chunk Index: {meta.get('chunk_index', 'N/A')}")
            print(f"\n--- 텍스트 내용 (앞부분 500자) ---")
            print(doc[:500])
            print("\n" + "-" * 80)

            # 첫 3줄만 자세히 분석
            lines = doc.split('\n')[:3]
            print(f"📝 첫 3줄 분석:")
            for j, line in enumerate(lines, 1):
                print(f"  {j}. {repr(line)}")
            print("=" * 80)
    else:
        print("⚠️ meeting_chunks 컬렉션에 데이터가 없습니다.")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
