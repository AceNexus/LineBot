import logging

from linebot.models import MessageEvent, TextMessage, TextSendMessage

from app.extensions import line_bot_api, handler

logger = logging.getLogger(__name__)


@handler.add(MessageEvent, message=TextMessage)
def process_text_message(event):
    try:
        message_text = event.message.text
        user_id = event.source.user_id

        logger.info(f"Received text message from {user_id}: {message_text}")

        # 在這裡處理文字訊息邏輯
        response_text = f"Your message was received: {message_text}"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )
    except Exception as e:
        logger.error(f"Error processing text message: {e}")
