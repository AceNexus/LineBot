import logging
import os

from flask import Flask

from app.api import init_app
from app.config import Config
from app.extensions import init_line_bot_api
from app.logger import setup_logger

logger = logging.getLogger(__name__)


def create_app():
    # 設定 Flask 應用
    app = Flask(__name__)

    # 將 Config 物件的設置加載到 Flask 應用配置
    app.config.from_object(Config)

    # 設定日誌格式
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    app.logger.setLevel(log_level)
    setup_logger(app)

    # 初始化 LINE Bot
    if not init_line_bot_api(Config.LINE_CHANNEL_ACCESS_TOKEN, Config.LINE_CHANNEL_SECRET):
        app.logger.error("Failed to initialize LINE Bot. Exiting...")
        exit(1)  # 如果初始化失敗，則退出應用

    # 初始化 API 藍圖
    init_app(app)

    # 導入處理器
    from app.handlers.line_message_handlers import process_text_message

    return app
