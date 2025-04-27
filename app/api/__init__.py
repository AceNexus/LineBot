from flask import Blueprint, jsonify

# 定義主藍圖
main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
def home():
    return 'LINE 訊息 Webhook 服務運行中！'

@main_blueprint.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# app/api/v1/__init__.py
from .v1.routes import api_v1_blueprint

def init_app(app):
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_v1_blueprint, url_prefix='/api/v1')

    app.logger.info("Blueprints registered and app initialized")