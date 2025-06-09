import logging
import time
from enum import Enum
from typing import Dict, Any, List, Union, Optional
from urllib.parse import parse_qs

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage,
    PostbackEvent
)

from app.extensions import line_bot_api, handler
from app.services import groq_service
from app.utils.english_words import (
    handle_english_word_input,
    get_english_difficulty_menu, get_english_count_menu,
    get_english_words
)
from app.utils.japanese_words import get_japanese_word
from app.utils.lumos import get_lumos
from app.utils.menu import get_menu
from app.utils.movie import get_movies
from app.utils.news import get_news_topic_menu, get_news_count_menu, get_news

logger = logging.getLogger(__name__)


class UserState(Enum):
    NORMAL = "normal"
    AWAITING_ENGLISH_WORD_COUNT = "awaiting_english_word_count"


"""定義命令別名"""
MENU_COMMANDS = ["0", "啊哇呾喀呾啦", "menu", "選單"]
NEWS_COMMANDS = ["1"]
MOVIE_COMMANDS = ["2"]
JAPANESE_WORD_COMMANDS = ["3"]
ENGLISH_WORD_COMMANDS = ["4"]
LUMOS_COMMANDS = ["路摸思", "lumos"]

# 按鈕冷卻時間（秒）
BUTTON_COOLDOWN = 3.0

"""用戶狀態追蹤字典"""
user_states: Dict[str, Dict[str, Any]] = {}

"""追蹤使用者最後操作時間"""
user_last_action_time: Dict[str, float] = {}


def check_button_cooldown(user_id: str) -> bool:
    """
    檢查使用者是否在冷卻時間內
    返回 True 表示可以操作，False 表示需要等待
    """
    current_time = time.time()
    last_action_time = user_last_action_time.get(user_id, 0)

    if current_time - last_action_time < BUTTON_COOLDOWN:
        return False

    user_last_action_time[user_id] = current_time
    return True


@handler.add(PostbackEvent)
def handle_postback(event):
    try:
        user_id = event.source.user_id

        # 檢查冷卻時間
        if not check_button_cooldown(user_id):
            reply_to_user(event.reply_token, "操作太快了，請稍等一下再試")
            return

        data = parse_qs(event.postback.data)
        action = data.get('action', [''])[0]
        news_topic = data.get('news_topic', [''])[0]
        news_count = data.get('news_count', [''])[0]
        english_difficulty = data.get('english_difficulty', [''])[0]
        english_count = data.get('english_count', [''])[0]

        logger.info(f"Received postback from {user_id}: {action}")

        if action == 'news':
            response = get_news_topic_menu()
        elif news_topic:
            response = get_news_count_menu(news_topic)
        elif news_count:
            topic_id, count = news_count.split('/')
            response = get_news(topic_id, int(count))
        elif action == 'movie':
            response = get_movies()
        elif action == 'japanese':
            response = get_japanese_word(user_id)
        elif action == 'english':
            response = get_english_difficulty_menu()
        elif english_difficulty:
            response = get_english_count_menu(english_difficulty)
        elif english_count:
            difficulty_id, count = english_count.split('/')
            response = get_english_words(user_id, int(difficulty_id), int(count))
        else:
            response = "無效的操作"

        reply_to_user(event.reply_token, response)

    except Exception as e:
        logger.error(f"處理 postback 事件時發生錯誤: {e}", exc_info=True)
        reply_to_user(event.reply_token, "系統忙碌中，請稍後重試。若問題持續發生，請聯繫客服，謝謝您的耐心!")


@handler.add(MessageEvent, message=TextMessage)
def process_text_message(event):
    try:
        message_text = event.message.text
        user_id = event.source.user_id
        logger.info(f"Received text message from {user_id}: {message_text}")

        response = process_user_input(user_id, message_text)
        reply_to_user(event.reply_token, response)

    except Exception as e:
        logger.error(f"處理文字訊息時發生錯誤: {e}", exc_info=True)
        reply_to_user(event.reply_token, "系統忙碌中，請稍後重試。若問題持續發生，請聯繫客服，謝謝您的耐心!")


def process_user_input(user_id: str, message_text: str) -> Union[str, TextSendMessage, FlexSendMessage, List]:
    msg = message_text.strip().lower()
    user_data = get_user_data(user_id)
    current_state = user_data["state"]

    if msg in MENU_COMMANDS:
        clear_user_state(user_id)
        return get_menu()

    if current_state == UserState.AWAITING_ENGLISH_WORD_COUNT:
        return handle_english_word_count_input(user_id, msg)

    if current_state == UserState.NORMAL:
        command_response = handle_command(user_id, msg)
        if command_response is not None:
            return command_response

    clear_user_state(user_id)
    return groq_service.chat_with_groq(user_id, message_text)


def handle_command(user_id: str, msg: str) -> Optional[Union[str, TextSendMessage, FlexSendMessage, List]]:
    if msg in NEWS_COMMANDS:
        return get_news_topic_menu()
    elif msg in MOVIE_COMMANDS:
        return get_movies()
    elif msg in JAPANESE_WORD_COMMANDS:
        return get_japanese_word(user_id)
    elif msg in ENGLISH_WORD_COMMANDS:
        return get_english_difficulty_menu()
    elif msg in LUMOS_COMMANDS:
        return get_lumos()
    return None


def handle_english_word_count_input(user_id: str, msg: str) -> Union[str, FlexSendMessage, List]:
    """處理英文單字數量輸入"""
    result, success = handle_english_word_input(user_id, msg)

    # 只有成功時才清除狀態，失敗時保持 AWAITING_ENGLISH_WORD_COUNT 狀態，讓用戶重新輸入
    if success:
        clear_user_state(user_id)

    return result


def get_user_data(user_id: str) -> Dict[str, Any]:
    """獲取用戶數據，如果不存在則創建"""
    if user_id not in user_states:
        user_states[user_id] = {
            "state": UserState.NORMAL,
            "last_action_time": 0
        }
    return user_states[user_id]


def set_user_state(user_id: str, state: UserState):
    """設置用戶狀態"""
    user_data = get_user_data(user_id)
    user_data["state"] = state


def clear_user_state(user_id: str):
    """清除用戶狀態"""
    if user_id in user_states:
        user_states[user_id]["state"] = UserState.NORMAL


def reply_to_user(reply_token: str, message: Union[str, TextSendMessage, FlexSendMessage, List]):
    """回覆用戶訊息"""
    if isinstance(message, list):
        line_bot_api.reply_message(reply_token, message)
    else:
        if isinstance(message, str):
            message = TextSendMessage(text=message)
        line_bot_api.reply_message(reply_token, message)
