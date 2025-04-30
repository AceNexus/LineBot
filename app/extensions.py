# app/extensions.py
import logging

from linebot import LineBotApi, WebhookHandler

line_bot_api = None
handler = None
logger = logging.getLogger(__name__)


def init_line_bot_api(channel_access_token, channel_secret):
    global line_bot_api, handler

    # 檢查 channel_access_token 和 channel_secret 是否提供
    if not channel_access_token:
        logger.error("LINE_CHANNEL_ACCESS_TOKEN not provided")
        return False

    if not channel_secret:
        logger.error("LINE_CHANNEL_SECRET not provided")
        return False

    try:
        # 初始化 LINE Bot API 和 Handler
        line_bot_api = LineBotApi(channel_access_token)
        handler = WebhookHandler(channel_secret)

        # 檢查 handler 是否已經被正確初始化
        if handler is None:
            logger.error("Failed to initialize LINE Bot Handler")
            return False

        logger.info("LINE Bot initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing LINE Bot: {e}")
        return False


def get_handler():
    return handler


def get_line_bot_api():
    return line_bot_api
