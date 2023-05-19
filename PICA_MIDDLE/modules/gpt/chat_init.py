import faiss
import os
import urllib.request
from modules.aws import AwsQuery

from langchain.docstore import InMemoryDocstore
from langchain.vectorstores import FAISS
from langchain.memory import VectorStoreRetrieverMemory
from langchain.embeddings.openai import OpenAIEmbeddings


OPENAI_API_KEY = "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"
HUGGINGFACEHUB_API_TOKEN = ""
SERPAPI_API_KEY = ""

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
os.environ["SERPAPI_API_KEY"] = SERPAPI_API_KEY

EMBEDDING_SIZE = 1536  # OpenAIEmbeddings 의 차원 수(한국어도 처리해주는지 확인 필요)
embedding_fn = OpenAIEmbeddings().embed_query

aws = AwsQuery()


def make_static_vecDB(user_id, user, name, mbti, age):
    """
    사전에 질문과 답변 프리셋을 미리 구성해놓고 생성
    사전 DB는 초기에 저장된 질문 답변 외에 추가되지 않음
    """
    index = faiss.IndexFlatL2(EMBEDDING_SIZE)
    vectorstore = FAISS(embedding_fn, index, InMemoryDocstore({}), {})

    preset = [
        ("안녕", "안녕!"),
        ("너 이름이 뭐야", f"내 이름은 {name}야"),
        ("너 누구야", f"난 {name}야"),
        ("너 성격이 어때?", f"내 mbti는 {mbti}야"),
        ("너 mbti가 뭐야", f"내 mbti는 {mbti}야"),
        ("너 몇살이야?", f"난 {age}살이야"),
    ]

    vectorstore.add_texts([q for q, _ in preset], [{"answer": a} for _, a in preset])

    vectorstore.save_local(f"{user_id}/static")


def make_memory_vecDB(user_id, user, name):
    """
    기억 DB를 생성
    기억 DB는 사용자가 입력한 값과 챗봇의 대답이 3세트씩 Document 단위로 저장함
    """
    text = None
    index = faiss.IndexFlatL2(EMBEDDING_SIZE)
    vectorstore = FAISS(embedding_fn, index, InMemoryDocstore({}), {})
    retriever = vectorstore.as_retriever(search_kwargs=dict(k=1))
    memory = VectorStoreRetrieverMemory(retriever=retriever, return_docs=False)
    # s3 에서 이전 대화 요약 가져오기
    with urllib.request.urlopen(
        aws.CLOUD_FLONT_CDN + f"/{user_id}/log_summary/yesterday.txt"
    ) as response:
        yesterday_txt = response.read().decode("utf-8")

    memory.save_context({"시간": "어제"}, {"대화": yesterday_txt})

    vectorstore.save_local(f"{user_id}/memory")
