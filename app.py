import os
import sys
import logging
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 獲取 LINE Bot 憑證
try:
    line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', ''))
    handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET', ''))
    
    if not os.environ.get('LINE_CHANNEL_ACCESS_TOKEN') or not os.environ.get('LINE_CHANNEL_SECRET'):
        logger.warning("LINE credentials not set. Check environment variables.");
except Exception as e:
    logger.error(f"Error initializing LINE Bot API: {e}")
    sys.exit(1)

@app.route('/')
def home():
    return 'LINE Message Webhook service is running!'

@app.route('/webhook', methods=['POST'])
def webhook():
    # 獲取 X-Line-Signature headers
    signature = request.headers.get('X-Line-Signature', '')
    
    # 獲取請求主體
    body = request.get_data(as_text=True)
    
    logger.info(f"Received webhook request: {body}")
    
    try:
        # 驗證簽名
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        abort(500)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    try:
        message_text = event.message.text
        user_id = event.source.user_id
        
        logger.info(f"Received message from {user_id}: {message_text}")
        reply_text = f"Your message has been received: {message_text}"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        logger.error(f"處理消息時出錯: {e}")

# 添加健康檢查端點
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)