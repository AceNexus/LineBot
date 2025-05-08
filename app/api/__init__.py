import logging

from flask import jsonify
from flask import request, Blueprint

from .v1 import api_v1_blueprint
from ..extensions import get_handler

main_blueprint = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


@main_blueprint.route('/')
def home():
    return 'LINE 訊息 Webhook 服務運行中！'


@main_blueprint.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200


@main_blueprint.route('/webhook', methods=['POST'])
def webhook():
    handler = get_handler()
    if handler is None:
        logger.error("Handler is not initialized.")
        return "Handler not initialized", 500

    try:
        body = request.get_data(as_text=True)
        signature = request.headers['X-Line-Signature']
        handler.handle(body, signature)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return "Error", 500

    return "OK"


def init_app(app):
    app.register_blueprint(main_blueprint)
    logger.info("main_blueprint registered and app initialized")

    app.register_blueprint(api_v1_blueprint, url_prefix='/v1')
    logger.info("api_v1_blueprint registered and app initialized")
