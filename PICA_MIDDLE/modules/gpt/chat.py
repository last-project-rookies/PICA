import os
import time
import json
import re
import asyncio

from langchain import ConversationChain
from langchain.schema import Document
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage
from langchain.memory import ConversationBufferMemory, VectorStoreRetrieverMemory
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings

from modules.gpt.chat_init import make_memory_vecDB, make_static_vecDB

# mbti Prompt json 파일 로드
with open("./modules/gpt/mbti_en.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# open ai key
OPENAI_API_KEY = "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"
HUGGINGFACEHUB_API_TOKEN = ""
SERPAPI_API_KEY = ""

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
os.environ["SERPAPI_API_KEY"] = SERPAPI_API_KEY

# user에게 입력받는 값
user = None
name = None
mbti = None
age = None
user_id = None

# 대화 3개씩 벡터에 넣을 때 사용
check_vector_update = 0
conversation_tmp = ""

# LLM 모델 정의
chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)


# 프롬프트를 역할별로 나눔
PERSONA_TEMPLATE = None
CURRENT_TEMPLATE = None


def make_converChain():
    """
    ConversationChain 객체를 만드는 함수
    """

    TOTAL_TEMPLATE = PERSONA_TEMPLATE + CURRENT_TEMPLATE
    PROMPT = PromptTemplate(input_variables=["history", "input"], template=TOTAL_TEMPLATE)
    conversation = ConversationChain(
        llm=chat,
        verbose=True,
        memory=ConversationBufferMemory(human_prefix=user, ai_prefix=name),
        prompt=PROMPT,
    )

    return conversation


def update_conversation(conversation, relevant_conversation=""):
    """
    사용자가 입력하면 입력한 내용과 가장 유사한 문서를 벡터DB에서 검색하여 프롬프트에 반영
    """

    RELEVANT_TEMPLATE = f"""
    Relevant pieces of previous conversation:
        {relevant_conversation}
        (You do not need to use these pieces of information if not relevant)
    """

    TOTAL_TEMPLATE = PERSONA_TEMPLATE + RELEVANT_TEMPLATE + CURRENT_TEMPLATE
    conversation.prompt.template = TOTAL_TEMPLATE


def make_vecDB():
    """
    사전 DB와 기억 DB 생성
    """
    make_static_vecDB(user_id, user, name, mbti, age)
    make_memory_vecDB(user_id, user, name)


def load_vecDB():
    """
    생성한 DB를 로드
    사용자가 대화를 종료하고 다시 시작할 때 실행되어야함
    """
    memory_vectorstore = FAISS.load_local(f"{user_id}/memory", OpenAIEmbeddings())
    static_vectorstore = FAISS.load_local(f"{user_id}/static", OpenAIEmbeddings())

    return memory_vectorstore, static_vectorstore


def generate_answer(text, conversation, memory_vectorstore, static_vectorstore):
    """
    대답 생성하는 함수
    """
    global conversation_tmp
    global check_vector_update

    similarity_conversation = static_vectorstore.similarity_search_with_score(text, k=1)[0]

    if similarity_conversation[1] < 0.1:
        answer = similarity_conversation[0].metadata["answer"]
        conversation.memory.chat_memory.messages.append(HumanMessage(content=text))
        conversation.memory.chat_memory.messages.append(AIMessage(content=answer))
        print("(Vector DB) ", end="")
    else:
        relevant_conversation = memory_vectorstore.similarity_search_with_score(text, k=1)[0][
            0
        ].page_content
        update_conversation(conversation, relevant_conversation)
        answer = conversation.predict(input=text)
        print("(GPT) ", end="")

    conversation_tmp += f"{user}: {text}\n{name}: {answer}\n"
    check_vector_update += 1

    if check_vector_update >= 3:
        memory_vectorstore.add_documents(documents=[Document(page_content=conversation_tmp)])
        check_vector_update = 0
        conversation_tmp = ""

    conversation.memory.chat_memory.messages = conversation.memory.chat_memory.messages[-4:]

    return answer


def exit_chat(memory_vectorstore):
    """
    사용자가 채팅 종료하면 기억 DB에 반영
    """
    memory_vectorstore.save_local(f"{user_id}/memory")


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


# 유저로부터 가져온 정보 세팅
def setting(user_get="이건우", name_get="이루다", mbti_get="ISTJ", age_get="22", user_id_get="userid"):
    """
    유저로부터 가져온 정보 세팅
    """
    global PERSONA_TEMPLATE, CURRENT_TEMPLATE, user, name, mbti, age, user_id
    user = user_get
    name = name_get
    mbti = mbti_get
    age = age_get
    user_id = user_id_get
    PERSONA_TEMPLATE = f"""
        System:
            {data[mbti]}

        Persona:
            name: {name}
            MBTI: {mbti}
            age: {age}
        """
    CURRENT_TEMPLATE = f"""
        Current conversation:
        {name} uses informal korean.(무조건 반말을 사용한다)
            {{history}}
            {user}: {{input}}
            {name}: """
    conversation = make_converChain()
    make_vecDB()
    memory_vectorstore, static_vectorstore = load_vecDB()
    return conversation, memory_vectorstore, static_vectorstore


# 대화 시작
async def gpt_call(voice, conversation, memory_vectorstore, static_vectorstore):
    answer = generate_answer(voice, conversation, memory_vectorstore, static_vectorstore)
    print(answer)
    return remove_emoji(answer)


if __name__ == "__main__":
    conversation, memory_vectorstore, static_vectorstore = setting()
    answer = asyncio.run(gpt_call("안녕", conversation, memory_vectorstore, static_vectorstore))
    answer = asyncio.run(
        gpt_call("어제 여행 어디갔지?", conversation, memory_vectorstore, static_vectorstore)
    )
    answer = asyncio.run(
        gpt_call("니 성격이 머야?", conversation, memory_vectorstore, static_vectorstore)
    )
    answer = asyncio.run(
        gpt_call("어제 여행 어디갔지?", conversation, memory_vectorstore, static_vectorstore)
    )
    answer = asyncio.run(gpt_call("멍청아", conversation, memory_vectorstore, static_vectorstore))
