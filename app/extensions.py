import logging
from linebot import LineBotApi, WebhookHandler

line_bot_api = None
handler = None

def init_line_bot_api(channel_access_token, channel_secret):
    global line_bot_api, handler
    
    try:
        line_bot_api = LineBotApi(channel_access_token)
        handler = WebhookHandler(channel_secret)
        
        logging.info("LineBotApi and WebhookHandler successfully initialized.")
    except Exception as e:
        logging.error(f"Error initializing LineBotApi or WebhookHandler: {e}")
