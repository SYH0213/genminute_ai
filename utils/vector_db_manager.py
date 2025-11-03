
import chromadb
import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from dotenv import load_dotenv

from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
from langchain_classic.chains.query_constructor.base import AttributeInfo


# 이 파일의 상위 디렉토리에 있는 .env 파일을 찾아 로드
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class VectorDBManager:
    COLLECTION_NAMES = {
        'chunks': 'meeting_chunks',
        'subtopic': 'meeting_subtopic',
    }

    def __init__(self, persist_directory="./database/vector_db"):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")

        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_function = OpenAIEmbeddings()

        # Initialize LLM for SelfQueryRetriever
        self.llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0)

        self.vectorstores = {
            key: Chroma(
                client=self.client,
                collection_name=name,
                embedding_function=self.embedding_function,
            )
            for key, name in self.COLLECTION_NAMES.items()
        }

        # Define metadata field information for SelfQueryRetriever
        self.metadata_field_infos = {
            "chunks": [
                AttributeInfo(name="meeting_id", description="The unique identifier for the meeting", type="string"),
                AttributeInfo(name="dialogue_id", description="The unique identifier for the dialogue within the meeting", type="string"),
                AttributeInfo(name="title", description="The title of the meeting", type="string"),
                AttributeInfo(name="meeting_date", description="The date of the meeting in ISO format (YYYY-MM-DD)", type="string"),
                AttributeInfo(name="audio_file", description="The name of the audio file for the meeting", type="string"),
            ],
            "subtopic": [
                AttributeInfo(name="meeting_id", description="The unique identifier for the meeting", type="string"),
                AttributeInfo(name="meeting_title", description="The title of the meeting", type="string"),
                AttributeInfo(name="meeting_date", description="The date of the meeting in ISO format (YYYY-MM-DD)", type="string"),
                AttributeInfo(name="audio_file", description="The name of the audio file for the meeting", type="string"),
                AttributeInfo(name="main_topic", description="The main topic of the summarized sub-chunk", type="string"),
                AttributeInfo(name="summary_index", description="The index of the summary sub-chunk", type="integer"),
            ],
        }

        # Define document content descriptions for SelfQueryRetriever
        self.document_content_descriptions = {
            "chunks": "Full transcript of a meeting",
            "subtopic": "Summarized sub-topic of a meeting transcript",
        }

        print(f"✅ VectorDBManager for collections {list(self.COLLECTION_NAMES.values())} initialized.")

    def add_meeting_as_chunk(self, meeting_id, title, meeting_date, audio_file, full_text):
        """하나의 회의 전체를 단일 청크로 DB에 저장합니다."""
        chunk_vdb = self.vectorstores['chunks']

        metadata = {
            "meeting_id": meeting_id,
            "dialogue_id": meeting_id,  # 전체 문서를 나타내는 청크이므로 meeting_id를 사용
            "title": title,
            "meeting_date": meeting_date,
            "audio_file": audio_file
        }

        chunk_vdb.add_texts(texts=[full_text], metadatas=[metadata], ids=[meeting_id])
        print(f"Added full text of meeting {meeting_id} as a single chunk to meeting_chunks DB.")


    def add_meeting_as_subtopic(self, meeting_id, title, meeting_date, audio_file, summary_content):
        """스크립트 전체를 소주제별 청크로 DB에 저장합니다."""

        
        # 1. 생성된 요약을 주제별로 파싱
        # "### "로 분리하되, 첫 번째 요소가 공백일 경우를 대비해 filter(None, ...) 사용
        summary_chunks = summary_content.split('\n### ')
        summary_chunks = [chunk.strip() for chunk in summary_chunks if chunk.strip()]
        
        # 첫 번째 청크에 "### "가 누락되었을 수 있으므로, 첫 번째 청크만 따로 처리
        # if summary_chunks and not summary_chunks[0].startswith('###'):
        #      # 첫번째 청크가 ###로 시작하지 않으면 ###를 붙여준다.
        #      if summary_chunks[0].count('\n') > 0:
        #          summary_chunks[0] = '### ' + summary_chunks[0]

        print("===============summary_chunks=================")
        print(summary_chunks)
        
        # 2. 각 요약 chunk를 Summary_Analysis_DB에 저장
        subtopic_vdb = self.vectorstores['subtopic']
        chunk_texts = []
        chunk_metadatas = []
        chunk_ids = []

        for i, chunk in enumerate(summary_chunks):
            # '### '가 없는 경우를 대비하여, 첫 줄을 main_topic으로 추출
            lines = chunk.split('\n')
            main_topic = lines[0].replace('### ', '').strip()
            
            # 실제 저장될 내용은 '### '를 포함한 전체 청크
            full_chunk_content = '### ' + chunk if not chunk.startswith('###') else chunk

            chunk_texts.append(full_chunk_content)
            chunk_metadatas.append({
                "meeting_id": meeting_id,
                "meeting_title": title,
                "meeting_date": meeting_date,
                "audio_file": audio_file,
                "main_topic": main_topic,
                "summary_index": i
            })
            chunk_ids.append(f"{meeting_id}_summary_{i}")

        if chunk_texts:
            subtopic_vdb.add_texts(texts=chunk_texts, metadatas=chunk_metadatas, ids=chunk_ids)
            print(f"📄 요약 결과 {len(chunk_texts)}개를 Summary_Analysis_DB에 저장했습니다.")
            return summary_chunks
        else:
            print("⚠️ 요약 결과에서 유효한 청크를 찾지 못했습니다.")



    
    
    def search(self, db_type: str, query: str, k: int = 5, retriever_type: str = "similarity", filter_criteria: dict = None) -> list:
        """
        지정된 DB에서 쿼리와 필터 조건을 사용하여 문서를 검색합니다.

        Args:
            db_type (str): 검색할 DB 타입 ('chunk', 'full_doc', 'summary', 'template').
            query (str): 검색할 텍스트 쿼리.
            k (int, optional): 반환할 결과의 수. Defaults to 5.
            retriever_type (str, optional): 사용할 리트리버 타입 ('similarity', 'mmr', 'self_query'). Defaults to "similarity".
            filter_criteria (dict, optional): 메타데이터 필터링 조건 (예: {'meeting_id': '...', 'audio_file': '...'}). Defaults to None.

        Returns:
            list: LangChain Document 객체 리스트.
        """
        # 1. Validate inputs
        if db_type not in self.vectorstores:
            raise ValueError(f"Unknown db_type: {db_type}. Available types are {list(self.vectorstores.keys())}")
        if retriever_type not in ["similarity", "mmr", "self_query"]:
            raise ValueError(f"Unsupported retriever_type: {retriever_type}. Choose from 'similarity', 'mmr', 'self_query'.")

        vdb = self.vectorstores[db_type]
        results = []

        # 2. Handle 'similarity' and 'mmr' retrievers
        if retriever_type in ["similarity", "mmr"]:
            search_kwargs = {'k': k}
            if filter_criteria:
                search_kwargs['filter'] = filter_criteria
            
            retriever = vdb.as_retriever(
                search_type=retriever_type,
                search_kwargs=search_kwargs
            )
            results = retriever.invoke(query)

        # 3. Handle 'self_query' retriever
        elif retriever_type == "self_query":
            metadata_info = self.metadata_field_infos[db_type]
            doc_description = self.document_content_descriptions[db_type]
            
            retriever = SelfQueryRetriever.from_llm(
                self.llm,
                vdb,
                doc_description,
                metadata_info,
                verbose=True,
                base_filter=filter_criteria  # Apply the hard filter here
            )
            results = retriever.invoke(query)
            
        print(f"Found {len(results)} documents from '{self.COLLECTION_NAMES[db_type]}' for query: '{query}'")
        return results

    
    def delete_from_collection(self, db_type, meeting_id=None, audio_file=None, title=None):
        """
        지정된 벡터 DB 컬렉션에서 항목을 삭제합니다.
        meeting_id, audio_file, title 중 하나 이상이 제공되면 해당 조건에 맞는 항목을 삭제합니다.
        아무것도 제공되지 않으면 해당 db_type의 전체 컬렉션을 삭제합니다.
        """
        if db_type not in self.vectorstores:
            raise ValueError(f"Unknown db_type: {db_type}. Must be one of {list(self.COLLECTION_NAMES.keys())}")

        collection = self.client.get_or_create_collection(name=self.COLLECTION_NAMES[db_type])

        filters = {}
        if meeting_id:
            filters["meeting_id"] = meeting_id
        if audio_file:
            filters["audio_file"] = audio_file
        if title:
            filters["title"] = title

        if filters:
            # 특정 필터가 있는 경우
            print(f"🗑️ Deleting from '{db_type}' collection with filters: {filters}")
            collection.delete(where=filters)
            print(f"✅ Deletion from '{db_type}' collection complete.")
        else:
            # 필터가 없는 경우, 전체 컬렉션 삭제
            print(f"⚠️ No specific filters provided. Deleting ALL items from '{db_type}' collection.")
            collection.delete(where={}) # deletes all items
            print(f"✅ All items deleted from '{db_type}' collection.")



# --- 싱글톤 인스턴스 생성 ---
# DB 파일은 minute_ai/database/vector_db 경로에 저장됩니다.
# vector_db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'vector_db')
vdb_manager = VectorDBManager()
