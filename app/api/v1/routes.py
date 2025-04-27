from flask import Blueprint, request, abort, jsonify
from app.extensions import line_bot_api, handler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import logging

api_v1_blueprint = Blueprint('api_v1', __name__)

logger = logging.getLogger(__name__)

@api_v1_blueprint.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    logger.info(f"Received webhook request: {body}")
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        abort(500)
    
    return 'OK'

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
