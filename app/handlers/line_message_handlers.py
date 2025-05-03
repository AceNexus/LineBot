import logging

from linebot.models import MessageEvent, TextMessage, TextSendMessage

from app.extensions import line_bot_api, handler
from app.services import groq_service
from app.utils.lumos import get_lumos
from app.utils.movie import get_movies
from app.utils.news import get_news
from app.utils.words import get_english_word, get_japanese_word

logger = logging.getLogger(__name__)


@handler.add(MessageEvent, message=TextMessage)
def process_text_message(event):
    try:
        message_text = event.message.text
        user_id = event.source.user_id

        logger.info(f"Received text message from {user_id}: {message_text}")

        normalized_text = message_text.strip().lower()

        # 根據用戶輸入選擇回應
        if normalized_text in ["0", "啊哇呾喀呾啦"]:
            response_text = (
                "請輸入數字選擇查詢項目：\n"
                "1. 新聞\n"
                "2. 電影\n"
                "3. 每日日文單字\n"
                "4. 每日英文單字"
            )
        elif normalized_text == "1":
            response_text = get_news()
        elif normalized_text == "2":
            response_text = get_movies()
        elif normalized_text == "3":
            response_text = get_japanese_word()
        elif normalized_text == "4":
            response_text = get_english_word()
        elif normalized_text in ["路摸思", "lumos"]:
            response_text = get_lumos()
        else:
            # 沒有符合條件的輸入，調用 Groq 語言模型處理
            response_text = groq_service.chat_with_groq(user_id, message_text)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )
    except Exception as e:
        logger.error(f"Error processing text message: {e}")
