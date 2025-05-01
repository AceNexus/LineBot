from groq import Groq

from app import Config

# 初始化 Groq client
client = Groq(api_key=Config.GROQ_API_KEY)

# 儲存每位使用者對話歷史的字典
user_sessions = {}


def chat_with_groq(user_id: str, message: str, model: str = "llama-3.3-70b-versatile") -> str:
    """
    使用 Groq 語言模型進行對話，支援多輪對話。
    :param user_id: 使用者 ID，用來識別每個使用者
    :param message: 使用者輸入訊息
    :param model: 使用的模型名稱，預設為 llama-3.3-70b-versatile
    :return: 模型回應的內容
    """
    # 初始化使用者對話紀錄
    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": "你是一個說中文的LINE聊天機器人"}
        ]

    # 加入使用者訊息
    user_sessions[user_id].append({"role": "user", "content": message})

    # 呼叫 Groq API
    response = client.chat.completions.create(
        messages=user_sessions[user_id],
        model=model,
    )

    # 取得模型回應
    reply = response.choices[0].message.content

    # 加入機器人回應
    user_sessions[user_id].append({"role": "assistant", "content": reply})

    return reply
