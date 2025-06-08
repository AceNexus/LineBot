import logging
from enum import Enum
from typing import Dict, Any, List, Union, Optional
from urllib.parse import parse_qs

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage,
    PostbackEvent
)

from app.extensions import line_bot_api, handler
from app.services import groq_service
from app.utils.english_words import generate_english_word_count_options, handle_english_word_input
from app.utils.japanese_words import get_japanese_word
from app.utils.lumos import get_lumos
from app.utils.menu import get_menu
from app.utils.movie import get_movies
from app.utils.news import generate_news_topic_options, handle_news_input

logger = logging.getLogger(__name__)


class UserState(Enum):
    NORMAL = "normal"
    AWAITING_NEWS_TOPIC_COUNT = "awaiting_news_topic_count"
    AWAITING_ENGLISH_WORD_COUNT = "awaiting_english_word_count"


"""定義命令別名"""
MENU_COMMANDS = ["0", "啊哇呾喀呾啦", "menu", "選單"]
NEWS_COMMANDS = ["1"]
MOVIE_COMMANDS = ["2"]
JAPANESE_WORD_COMMANDS = ["3"]
ENGLISH_WORD_COMMANDS = ["4"]
LUMOS_COMMANDS = ["路摸思", "lumos"]

"""用戶狀態追蹤字典"""
user_states: Dict[str, Dict[str, Any]] = {}


@handler.add(PostbackEvent)
def handle_postback(event):
    try:
        user_id = event.source.user_id
        data = parse_qs(event.postback.data)
        action = data.get('action', [''])[0]

        logger.info(f"Received postback from {user_id}: {action}")

        if action == 'news':
            set_user_state(user_id, UserState.AWAITING_NEWS_TOPIC_COUNT)
            response = generate_news_topic_options()
        elif action == 'movie':
            response = get_movies()
        elif action == 'japanese':
            response = get_japanese_word(user_id)
        elif action == 'english':
            set_user_state(user_id, UserState.AWAITING_ENGLISH_WORD_COUNT)
            response = generate_english_word_count_options()
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

    if current_state == UserState.AWAITING_NEWS_TOPIC_COUNT:
        return handle_news_topic_count_input(user_id, msg)

    if current_state == UserState.AWAITING_ENGLISH_WORD_COUNT:
        return handle_english_word_count_input(user_id, msg)

    if current_state == UserState.NORMAL:
        command_response = handle_command(user_id, msg)
        if command_response is not None:
            return command_response

    clear_user_state(user_id)
    return groq_service.chat_with_groq(user_id, message_text)


def get_user_data(user_id: str) -> Dict[str, Any]:
    if user_id not in user_states:
        user_states[user_id] = {
            "state": UserState.NORMAL,
            "context": {}
        }
    return user_states[user_id]


def set_user_state(user_id: str, state: UserState, context: Dict[str, Any] = None):
    user_data = get_user_data(user_id)
    user_data["state"] = state
    if context:
        user_data["context"].update(context)


def clear_user_state(user_id: str):
    user_states.pop(user_id, None)


def reply_to_user(reply_token: str, message: Union[str, TextSendMessage, FlexSendMessage, List]):
    if isinstance(message, str):
        message = TextSendMessage(text=message)

    valid_types = (TextSendMessage, FlexSendMessage)
    if not (isinstance(message, list) or isinstance(message, valid_types)):
        raise TypeError("不支援的訊息類型，請使用字串、TextSendMessage、FlexSendMessage 或這些物件的列表")

    line_bot_api.reply_message(reply_token, message)


def handle_news_topic_count_input(user_id: str, msg: str) -> Union[str, FlexSendMessage]:
    """處理新聞主題數量輸入"""
    result, success = handle_news_input(msg)

    # 只有成功時才清除狀態，失敗時保持 AWAITING_NEWS_TOPIC_COUNT 狀態，讓用戶重新輸入
    if success:
        clear_user_state(user_id)

    return result


def handle_english_word_count_input(user_id: str, msg: str) -> Union[str, FlexSendMessage, List]:
    """處理英文單字數量輸入"""
    result, success = handle_english_word_input(user_id, msg)

    # 只有成功時才清除狀態，失敗時保持 AWAITING_ENGLISH_WORD_COUNT 狀態，讓用戶重新輸入
    if success:
        clear_user_state(user_id)

    return result


def handle_command(user_id: str, msg: str) -> Optional[Union[str, TextSendMessage, FlexSendMessage, List]]:
    if msg in NEWS_COMMANDS:
        set_user_state(user_id, UserState.AWAITING_NEWS_TOPIC_COUNT)
        return generate_news_topic_options()

    elif msg in MOVIE_COMMANDS:
        return get_movies()

    elif msg in JAPANESE_WORD_COMMANDS:
        return get_japanese_word(user_id)

    elif msg in ENGLISH_WORD_COMMANDS:
        set_user_state(user_id, UserState.AWAITING_ENGLISH_WORD_COUNT)
        return generate_english_word_count_options()

    elif msg in LUMOS_COMMANDS:
        return get_lumos()

    return None
