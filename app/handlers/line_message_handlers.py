import logging
from datetime import datetime
from typing import List, Union
from urllib.parse import parse_qs

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage,
    PostbackEvent
)

from app.extensions import line_bot_api, handler
from app.services import groq_service
from app.services.groq_service import get_ai_status_flex, toggle_ai_status
from app.utils.english_subscribe import (
    get_subscription_menu,
    get_difficulty_menu,
    get_count_menu,
    get_time_menu,
    get_subscription_confirm,
    handle_subscription_time,
    handle_subscription_save,
    handle_subscription_view,
    handle_subscription_cancel
)
from app.utils.english_words import (
    get_english_difficulty_menu, get_english_count_menu,
    get_english_words
)
from app.utils.japanese_words import get_japanese_word
from app.utils.lumos import get_lumos
from app.utils.medication import (
    get_medication_menu, get_medication_list_flex, get_today_records,
    delete_medication, start_add_medication, is_adding_medication,
    set_medication_name, finish_add_medication, cancel_add_medication,
    get_add_medication_step, get_time_select_menu,
    mark_medication_taken
)
from app.utils.menu import get_menu
from app.utils.movie import get_movies
from app.utils.news import get_news_topic_menu, get_news_count_menu, get_news

logger = logging.getLogger(__name__)

"""定義命令別名"""
MENU_COMMANDS = ["0", "啊哇呾喀呾啦", "menu", "選單"]
LUMOS_COMMANDS = ["路摸思", "lumos"]


@handler.add(PostbackEvent)
def handle_postback(event):
    chat_id = event.source.group_id if event.source.type == 'group' else event.source.user_id

    try:
        data = parse_qs(event.postback.data)
        action = data.get('action', [''])[0]
        news_topic = data.get('news_topic', [''])[0]
        news_count = data.get('news_count', [''])[0]
        english_difficulty = data.get('english_difficulty', [''])[0]
        english_count = data.get('english_count', [''])[0]

        logger.info(f"Received postback from {chat_id}: {action}")

        if action == 'toggle_ai':
            toggle_ai_status(chat_id)
            response = get_ai_status_flex(chat_id)
        elif action == 'news':
            response = get_news_topic_menu()
        elif news_topic:
            response = get_news_count_menu(news_topic)
        elif news_count:
            topic_id, count = news_count.split('/')
            response = get_news(topic_id, int(count))
        elif action == 'movie':
            response = get_movies()
        elif action == 'japanese':
            response = get_japanese_word(chat_id)
        elif action == 'english':
            response = get_english_difficulty_menu()
        elif action == 'english_subscribe':
            response = get_subscription_menu()
        elif action == 'english_subscribe_setup':
            response = get_difficulty_menu()
        elif 'english_subscribe_difficulty' in data:
            difficulty_id = data['english_subscribe_difficulty'][0]
            response = get_count_menu(difficulty_id)
        elif 'english_subscribe_count' in data:
            difficulty_id, count = data['english_subscribe_count'][0].split('/')
            response = get_time_menu(difficulty_id, int(count))
        elif 'english_subscribe_time' in data:
            difficulty_id, count, selected_times = handle_subscription_time(data)
            response = get_subscription_confirm(difficulty_id, count, selected_times)
        elif 'english_subscribe_save' in data:
            response = handle_subscription_save(data, chat_id)
        elif action == 'english_subscribe_view':
            response = handle_subscription_view(chat_id)
        elif action == 'english_subscribe_cancel':
            response = handle_subscription_cancel(chat_id)
        elif english_difficulty:
            response = get_english_count_menu(english_difficulty)
        elif english_count:
            difficulty_id, count = english_count.split('/')
            response = get_english_words(chat_id, int(difficulty_id), int(count))
        elif action == 'medication_menu':
            response = get_medication_menu()
        elif action == 'med_list':
            response = get_medication_list_flex(chat_id)
        elif action == 'med_today':
            response = get_today_records(chat_id)
        elif action.startswith('delete_medication_'):
            med_id = int(action.replace('delete_medication_', ''))
            success = delete_medication(chat_id, med_id)
            if success:
                response = [
                    TextSendMessage(text="藥品已刪除"),
                    get_medication_list_flex(chat_id)
                ]
            else:
                response = TextSendMessage(text="刪除失敗，請重試")
        elif action == 'start_add_medication':
            start_add_medication(chat_id)
            response = TextSendMessage(text="請輸入藥品名稱：")
        elif action.startswith('add_medication_time='):
            time = action.replace('add_medication_time=', '')
            success, message = finish_add_medication(chat_id, time)
            if success:
                response = [
                    TextSendMessage(text=message),
                    get_medication_list_flex(chat_id)
                ]
            else:
                response = TextSendMessage(text=message)
        elif action == 'medication_confirm':
            user_id = data.get('user_id', [chat_id])[0]
            med_name = data.get('med_name', [''])[0]
            time_str = data.get('time', [''])[0]
            today = datetime.now().strftime("%Y-%m-%d")
            mark_medication_taken(user_id, med_name, time_str, today)
            reply_to_user(event.reply_token, TextSendMessage(text="已記錄您今日吃藥！"))
            return
        elif action == 'custom_time':
            response = TextSendMessage(text="請輸入自訂時間（格式：HH:MM，例如 08:30）：")
        elif action == 'cancel_add_medication':
            cancel_add_medication(chat_id)
            response = TextSendMessage(text="已取消新增藥品")
        else:
            response = TextSendMessage(text="這功能正在裝上輪子，還在趕來的路上")

        reply_to_user(event.reply_token, response)

    except Exception as e:
        logger.error(f"處理 postback 事件時發生錯誤: {e}", exc_info=True)
        reply_to_user(event.reply_token, "系統忙碌中，請稍後重試。若問題持續發生，請聯繫客服，謝謝您的耐心!")


@handler.add(MessageEvent, message=TextMessage)
def process_text_message(event):
    """處理文字訊息的主要入口點"""
    chat_id = event.source.group_id if event.source.type == 'group' else event.source.user_id
    message_text = event.message.text
    logger.info(f"[TextMessage] chat_id: {chat_id}, message: {message_text}")

    try:
        # 新增藥品互動流程
        if is_adding_medication(chat_id):
            step = get_add_medication_step(chat_id)

            if step == 1:
                # 步驟1：輸入藥品名稱
                name = message_text.strip()
                if not name:
                    reply_to_user(event.reply_token, TextSendMessage(text="藥品名稱不能為空，請重新輸入："))
                    return

                set_medication_name(chat_id, name)
                reply_to_user(event.reply_token, get_time_select_menu(chat_id))
                return

            elif step == 2:
                # 步驟2：輸入時間（自訂時間）
                time = message_text.strip()
                success, message = finish_add_medication(chat_id, time)

                if success:
                    reply_to_user(event.reply_token, [
                        TextSendMessage(text=message),
                        get_medication_list_flex(chat_id)
                    ])
                else:
                    reply_to_user(event.reply_token, TextSendMessage(text=message))
                return

        # 一般訊息處理
        response = process_user_input(chat_id, message_text)
        if response is not None:
            reply_to_user(event.reply_token, response)

    except Exception as e:
        logger.error(f"處理文字訊息時發生錯誤 (聊天室: {chat_id}): {e}", exc_info=True)
        reply_to_user(event.reply_token, "系統忙碌中，請稍後重試。若問題持續發生，請聯繫客服，謝謝您的耐心!")


def process_user_input(chat_id: str, message_text: str) -> Union[str, TextSendMessage, FlexSendMessage, List]:
    msg = message_text.strip().lower()

    if msg in MENU_COMMANDS:
        return get_menu()

    if msg in LUMOS_COMMANDS:
        return get_lumos()

    return groq_service.chat_with_groq(chat_id, message_text)


def reply_to_user(reply_token: str, message: Union[str, TextSendMessage, FlexSendMessage, List]):
    """回覆用戶訊息"""
    if isinstance(message, list):
        line_bot_api.reply_message(reply_token, message)
    else:
        if isinstance(message, str):
            message = TextSendMessage(text=message)
        line_bot_api.reply_message(reply_token, message)
