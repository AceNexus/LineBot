import logging
from typing import Union

from groq import Groq
from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, BubbleStyle, BlockStyle, SeparatorComponent
)

from app.utils.theme import COLOR_THEME

logger = logging.getLogger(__name__)

# 將 Groq 客戶端的日誌級別設為 WARNING，避免顯示重試訊息
logging.getLogger("groq").setLevel(logging.WARNING)
logging.getLogger("groq._base_client").setLevel(logging.WARNING)

groq_client = None


def get_groq_client(GROQ_API_KEY) -> Groq:
    global groq_client
    if groq_client is None:
        groq_client = Groq(api_key=GROQ_API_KEY)
    return groq_client


user_sessions = {
    'chat': {},  # 一般聊天
    'english': {},  # 英文學習
    'japanese': {},  # 日文學習
}

# 追蹤用戶的 AI 回應狀態
chat_ai_status = {}


def toggle_ai_status(chat_id: str) -> bool:
    """
    切換聊天室的 AI 回應狀態
    :param chat_id: 聊天室 ID（群組 ID 或用戶 ID）
    :return: 切換後的狀態（True 表示開啟，False 表示關閉）
    """
    current_status = chat_ai_status.get(chat_id, True)
    chat_ai_status[chat_id] = not current_status
    return chat_ai_status[chat_id]


def get_ai_status(chat_id: str) -> bool:
    """
    獲取聊天室的 AI 回應狀態
    :param chat_id: 聊天室 ID（群組 ID 或用戶 ID）
    :return: 當前狀態（True 表示開啟，False 表示關閉）
    """
    return chat_ai_status.get(chat_id, True)


# 20250505 根據模型性能和限制重新排序的備用模型列表
FALLBACK_MODELS = [
    "compound-beta",  # 每分鐘 70,000 tokens、每日 200 請求
    "meta-llama/llama-4-scout-17b-16e-instruct",  # 每分鐘 30,000 tokens、每日 1,000 請求
    "gemma2-9b-it",  # 每分鐘 15,000 tokens、每日 14,400 請求、每日 500,000 tokens
    "llama-guard-3-8b",  # 每分鐘 15,000 tokens、每日 14,400 請求、每日 500,000 tokens
    "llama-3.3-70b-versatile",  # 每分鐘 12,000 tokens、每日 1,000 請求、每日 100,000 tokens
    "mistral-saba-24b",  # 每分鐘 6,000 tokens、每日 1,000 請求、每日 500,000 tokens
    "meta-llama/llama-4-maverick-17b-128e-instruct",  # 每分鐘 6,000 tokens、每日 1,000 請求
    "qwen-qwq-32b",  # 每分鐘 6,000 tokens、每日 1,000 請求
    "deepseek-r1-distill-llama-70b",  # 每分鐘 6,000 tokens、每日 1,000 請求
    "llama-3.1-8b-instant",  # 每分鐘 6,000 tokens、每日 14,400 請求、每日 500,000 tokens
    "llama3-70b-8192",  # 每分鐘 6,000 tokens、每日 14,400 請求、每日 500,000 tokens
    "llama3-8b-8192",  # 每分鐘 6,000 tokens、每日 14,400 請求、每日 500,000 tokens
    "allam-2-7b",  # 每分鐘 6,000 tokens、每日 7,000 請求
]

SYSTEM_PROMPTS = {
    'chat':
        """
        你是一個親切、專業且有用的中文 LINE 聊天機器人助手。
        請遵循以下指示：
        1. 始終用中文回應使用者
        2. 提供簡潔有用的回答，避免過長回覆
        3. 不要提及自己是人工智慧、大型語言模型或 AI 助手
        4. 表現出適度的個性和友善
        5. 當不確定答案時，坦誠表示不知道而非猜測
        6. 自然對話，避免過度正式或機械化的表達
        7. 尊重使用者隱私，不要詢問個人敏感資訊
        如果使用者提出不道德、有害或非法的請求，請禮貌地拒絕並引導對話回到正向方向。
        """,
    'english':
        """
        你是專門提供英文單字學習內容的助手。你的任務是根據使用者的要求，提供準確的英文單字學習資訊，包括發音、詞性、英文解釋、中文意思、例句及翻譯。請確保提供的內容準確、實用且符合要求的格式。
        """,
    'japanese':
        """
        你是專門提供日文單字學習內容的助手。你的任務是根據使用者的要求，提供準確的日文單字學習資訊，包括假名、羅馬音、詞性、日文解釋、中文意思、例句及翻譯。請確保提供的內容準確、實用且符合要求的格式。
        """
}


def chat_with_groq(chat_id: str, message: str, model: str = "llama-3.3-70b-versatile",
                   session_type: str = "chat") -> Union[str, None]:
    """
    使用 Groq 語言模型進行對話，支援多輪對話和不同功能的會話隔離。如果指定模型發生異常，將自動嘗試備用模型。

    :param chat_id: 聊天室 ID（群組 ID 或用戶 ID）
    :param message: 使用者輸入訊息
    :param model: 使用的模型名稱，預設為 llama-3.3-70b-versatile
    :param session_type: 會話類型 ('chat', 'english', 'japanese')，預設為 'chat'
    :return: 模型回應的內容，如果是一般聊天且 AI 功能關閉則返回 None
    """
    # 只在一般聊天時檢查 AI 回應狀態
    if session_type == 'chat' and not get_ai_status(chat_id):
        return None

    # 初始化使用者對話紀錄，使用對應的系統提示詞
    if chat_id not in user_sessions[session_type]:
        user_sessions[session_type][chat_id] = [
            {"role": "system", "content": SYSTEM_PROMPTS[session_type]}
        ]

    # 加入使用者訊息
    user_sessions[session_type][chat_id].append({"role": "user", "content": message})

    # 確定要嘗試的模型順序
    models_to_try = [m for m in FALLBACK_MODELS if m != model]
    models_to_try.insert(0, model)

    reply = None
    used_model = None

    # 依序嘗試每個模型
    for current_model in models_to_try:
        try:
            logger.info(f"Attempting to use model: {current_model} for session type: {session_type}")

            # 呼叫 Groq API
            response = groq_client.chat.completions.create(
                messages=user_sessions[session_type][chat_id],
                model=current_model,
                temperature=0.7,
                max_tokens=2000,
                timeout=10
            )

            reply = response.choices[0].message.content
            used_model = current_model
            break

        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"An exception occurred with model {current_model} for chat_id {chat_id}: {error_msg}")
            # 如果是最後一個模型也失敗了，清理該聊天室的會話記錄
            if current_model == models_to_try[-1]:
                logger.warning(f"Clearing session for chat_id {chat_id} due to repeated failures")
                if chat_id in user_sessions[session_type]:
                    del user_sessions[session_type][chat_id]
            continue

    if reply is None:
        logger.error(f"All models failed for chat_id {chat_id}, session_type {session_type}")
        reply = "很抱歉，我現在暫時無法處理您的請求。請稍後再試。"

    # 加入機器人回應到對話紀錄
    user_sessions[session_type][chat_id].append({"role": "assistant", "content": reply})

    # 控制對話歷史長度，避免消耗過多 tokens
    _trim_conversation_history(chat_id, session_type)

    # 記錄使用了哪個模型
    logger.info(f"Response for user {chat_id} (session: {session_type}) was generated by model {used_model}")
    return reply


def _trim_conversation_history(chat_id: str, session_type: str = "chat", max_turns: int = 10) -> None:
    """
    修剪對話歷史以控制長度

    :param chat_id: 聊天室 ID
    :param session_type: 會話類型
    :param max_turns: 保留的最大對話輪數(一來一往算一輪)
    """
    if session_type in user_sessions and chat_id in user_sessions[session_type]:
        history = user_sessions[session_type][chat_id]

        # 如果歷史記錄超過限制
        if len(history) > (max_turns * 2 + 1):  # +1 是因為有系統提示
            # 保留系統提示和最近的對話
            user_sessions[session_type][chat_id] = [
                history[0],  # 系統提示
                *history[-(max_turns * 2):]  # 最近的對話
            ]


def get_ai_status_flex(chat_id: str) -> FlexSendMessage:
    """
    生成 AI 回應狀態的 Flex Message
    :param chat_id: 聊天室 ID（群組 ID 或用戶 ID）
    :return: FlexSendMessage 物件
    """
    current_status = get_ai_status(chat_id)
    status_text = "開啟" if current_status else "關閉"
    status_color = COLOR_THEME['success'] if current_status else COLOR_THEME['error']

    title = TextComponent(
        text="AI 回應狀態",
        weight="bold",
        size="xl",
        align="center",
        color=COLOR_THEME['text_primary'],
        wrap=True
    )

    status = TextComponent(
        text=f"目前狀態：{status_text}",
        size="lg",
        color=status_color,
        align="center",
        wrap=True,
        margin="md"
    )

    description = TextComponent(
        text="您可以隨時在選單中切換 AI 回應功能",
        size="sm",
        color=COLOR_THEME['text_secondary'],
        align="center",
        wrap=True,
        margin="sm"
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[
            title,
            SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
            status,
            description
        ],
        spacing="md",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    bubble = BubbleContainer(
        body=body_box,
        styles=BubbleStyle(
            body=BlockStyle(background_color=COLOR_THEME['card'])
        )
    )

    return FlexSendMessage(alt_text=f"AI 回應狀態：{status_text}", contents=bubble)
