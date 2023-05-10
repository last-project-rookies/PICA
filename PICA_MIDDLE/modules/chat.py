from EdgeGPT import Chatbot, ConversationStyle
import asyncio
import re


# bing 대답 생성
async def being_call(data):
    """
    - descript = bing api 호출 및 처리
    - arg
        - data :`string` = voice 텍스트 문자
    - return
        - total_response : `string` = 이모티콘 제거 bing 대답 문자
    """
    bot = Chatbot(cookie_path="cookies.json")
    total_response = ""
    print("질문 : " + data)
    response = await bot.ask(
        prompt="자기소개 생략하고, 대답 안해도 되고, 50자 이내로 말해줘" + data,
        conversation_style=ConversationStyle.creative,
        wss_link="wss://sydney.bing.com/sydney/ChatHub",
    )

    for message in response["item"]["messages"]:
        if message["author"] == "bot" and message.get("text"):
            bot_response = message["text"]
            total_response += bot_response

    await bot.close()
    print("대답 : ", total_response)
    return remove_emoji(total_response)


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


if __name__ == "__main__":
    answer = asyncio.run(being_call("안녕하세요"))
    # answer = answer.encode("utf-8", "ignore").decode("utf-8")
    answer = remove_emoji(answer)
    print(answer)
