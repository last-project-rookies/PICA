# 요약
from langchain.docstore.document import Document

import os
import faiss
import time

from langchain import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.memory import (
    ConversationSummaryMemory,
    ChatMessageHistory,
    VectorStoreRetrieverMemory,
)

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.docstore import InMemoryDocstore
import re
import asyncio
import openai
import json

OPENAI_API_KEY = "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"
HUGGINGFACEHUB_API_TOKEN = ""
SERPAPI_API_KEY = ""

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
os.environ["SERPAPI_API_KEY"] = SERPAPI_API_KEY

chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
history = ChatMessageHistory()

# mbti_energy = ["E", "I"]
# mbti_information = ["S", "N"]
# mbti_decision = ["T", "F"]
# mbti_lifestyle = ["J", "P"]

# user = "김성언"
# name = "이루다"
# mbti = mbti_energy[1] + mbti_information[0] + mbti_decision[0] + mbti_lifestyle[0]
# age = "22"

# embedding_size = 1536  # Dimensions of the OpenAIEmbeddings
# index = faiss.IndexFlatL2(embedding_size)
# embedding_fn = OpenAIEmbeddings().embed_query
# vectorstore = FAISS(embedding_fn, index, InMemoryDocstore({}), {})
# retriever = vectorstore.as_retriever(search_kwargs=dict(k=3))
# memory = VectorStoreRetrieverMemory(retriever=retriever, return_docs=False)
# memory.save_context({"input": "안녕"}, {"output": "안녕!"})
# memory.save_context({"input": "노래 좋아해?"}, {"output": "노래 좋아하지"})

# An example is as follows:
# {{
# 'answer': answer to user's words,
# 'user_emotion': {{ 'happiness': 0.1, 'sad': 0.2, ... }},
# 'answer_emotion': Feeling for an answer (either happiness, sadness, or anger)
# }}


chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
# history = ChatMessageHistory()

embedding_size = 1536  # Dimensions of the OpenAIEmbeddings
index = faiss.IndexFlatL2(embedding_size)
embedding_fn = OpenAIEmbeddings().embed_query
vectorstore = FAISS(embedding_fn, index, InMemoryDocstore({}), {})
retriever = vectorstore.as_retriever(search_kwargs=dict(k=3))
memory = VectorStoreRetrieverMemory(retriever=retriever, return_docs=False)
memory.save_context({"input": "안녕"}, {"response": "안녕!"})
memory.save_context({"input": "노래 좋아해?"}, {"response": "노래 좋아하지"})


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


# 텍스트 기반 감정 분석 with chatgpt
async def user_chat_emotion(user_content):
    # 감정 분석 Prompt
    system_content = """
        I want you to help me to do text-based emotion analysis. 

        Please analyze its emotion and express it with numbers.
        emotion(rates of happiness, excited, sadness, bored, disgust, anger, calm, comfortable)

        Provide them in JSON format with the following keys: emotion

        Examples:
        {"emotion": {"happiness":0.1,"excited":0.0,"sadness":0.9,"bored":0.0,"disgust":0.0,"anger":0.0,"calm":0.0,"comfortable":0.0}}

        Also, you should observe the format given in the example. 
        Don't add your comments, but answer right away.

    """

    # ChatGPT 감정 분석
    messages = []
    result = None
    messages.append({"role": "system", "content": f"{system_content}"})
    messages.append({"role": "user", "content": f"{user_content}"})
    try:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)

        assistant_content = completion.choices[0].message["content"].strip()
        result = json.loads(assistant_content)
    # 감정을 알수 없을경우 happy로 지정
    except Exception as e:
        print("emotion err : 감정을 확인할 수 없습니다")
        result = {
            "emotion": {
                "happiness": 1.0,
                "excited": 0.0,
                "sadness": 0.0,
                "bored": 0.0,
                "disgust": 0.0,
                "anger": 0.0,
                "calm": 0.0,
                "comfortable": 0.0,
            }
        }
    finally:
        return result


# 유동적 prompt 관리
def update_conversation(recent_input, recent_output, user, name, mbti, age):
    _DEFAULT_TEMPLATE = f"""
    System:
    You will talk to the user with the persona below.

    Persona:
    name: {name}
    MBTI: {mbti}
    age: {age}
    keywords of personality: active, progressive
    
    Please reply within 100 characters.
    
    Relevant pieces of previous conversation:
    {{history}}

    (You do not need to use these pieces of information if not relevant)

    Current conversation:

    {name} uses korean. 무조건 반말을 사용한다. Just generate answer of {name}.
    {user}: {recent_input[0]}
    {name}: {recent_output[0]}
    {user}: {recent_input[1]}
    {name}: {recent_output[1]}
    {user}: {{input}}
    {name}: """

    PROMPT = PromptTemplate(input_variables=["history", "input"], template=_DEFAULT_TEMPLATE)
    conversation = ConversationChain(
        llm=chat,
        memory=memory,
        verbose=True,
        prompt=PROMPT,
    )

    return conversation


text_arr = ["", ""]
answer_arr = ["", ""]


# gpt 함수 호출용
async def gpt_call(voice, user="이건우", name="이루다", mbti="istj", age="22"):
    global text_arr, answer_arr
    conversation = update_conversation(text_arr, answer_arr, user, name, mbti, age)
    text_arr.append(voice)
    s_time = time.time()
    answer = conversation.predict(input=text_arr[-1])
    answer_arr.append(answer)
    if len(text_arr) == 3:
        text_arr.pop(0)
        answer_arr.pop(0)
    e_time = time.time()
    print(f"대답: {answer} ({e_time - s_time:.2f}초)")
    return remove_emoji(answer)


# 이모티콘 제거
def remove_emoji(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)


# asyncio.run(gpt_call("너무 슬퍼"))
# tmp = asyncio.run(user_chat_emotion("시발아 죽고싶냐?"))
# print(tmp, type(tmp))
