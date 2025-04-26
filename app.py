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

# 使用環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
PORT = int(os.getenv('PORT', 8080))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# 設定日誌（logging）
if not hasattr(logging, LOG_LEVEL):
    print(f"Warning: Invalid LOG_LEVEL '{LOG_LEVEL}', falling back to 'INFO'")
    LOG_LEVEL = 'INFO'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL, logging.INFO)
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 取得 LINE Bot 憑證
try:
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
        logger.warning("LINE credentials not set. Please check environment variables.")
        # 繼續執行，允許本地測試或其他功能使用

    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN or '')
    handler = WebhookHandler(LINE_CHANNEL_SECRET or '')
except Exception as e:
    logger.error(f"Error initializing LINE Bot API: {e}")
    sys.exit(1)

@app.route('/')
def home():
    return 'LINE 訊息 Webhook 服務運行中！'

@app.route('/webhook', methods=['POST'])
def webhook():
    # 取得 X-Line-Signature 標頭
    signature = request.headers.get('X-Line-Signature', '')
    
    # 取得請求主體內容
    body = request.get_data(as_text=True)
    
    logger.info(f"Received webhook request: {body}")
    
    try:
        # 驗證簽名
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        abort(500)
    
    return 'OK'

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    try:
        message_text = event.message.text
        user_id = event.source.user_id
        
        logger.info(f"Received message from {user_id}: {message_text}")
        reply_text = f"Your message was received: {message_text}"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}")

# 新增健康檢查端點
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)