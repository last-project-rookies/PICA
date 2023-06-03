# 요약
import os

from langchain.docstore.document import Document
from langchain.chat_models import ChatOpenAI
from langchain.memory import (
    ChatMessageHistory,
)
from langchain.prompts import PromptTemplate
from langchain.embeddings.openai import OpenAIEmbeddings


OPENAI_API_KEY = "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"
HUGGINGFACEHUB_API_TOKEN = ""
SERPAPI_API_KEY = ""

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
os.environ["SERPAPI_API_KEY"] = SERPAPI_API_KEY

chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
history = ChatMessageHistory()

EMBEDDING_SIZE = 1536  # Dimensions of the OpenAIEmbeddings
embedding_fn = OpenAIEmbeddings().embed_query


# 요약 만들기
async def make_summary(texts):
    doc = Document(page_content=texts)
    prompt_template = """Write a concise summary of the following:
    "{text}"
    CONCISE SUMMARY IN KOREAN:"""
    PROMPT_SUMMARY = PromptTemplate(template=prompt_template, input_variables=["text"])
    from langchain.chains.summarize import load_summarize_chain

    chain = load_summarize_chain(chat, chain_type="stuff", prompt=PROMPT_SUMMARY)
    result = chain.run([doc])
    print(result)
    # 바이너리 데이터일 경우
    # with open("yesterday.txt", "w", encoding="UTF-8") as f:
    #     f.write(result)
    return result
