from flask import request, abort
from app.extensions import handler
from linebot.exceptions import InvalidSignatureError
import logging

logger = logging.getLogger(__name__)

def process_line_webhook():
    signature = request.headers.get('X-Line-Signature', '')
    request_body = request.get_data(as_text=True)

    logger.info(f"Received webhook request: {request_body}")

    try:
        handler.handle(request_body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        abort(500)

    return 'OK'