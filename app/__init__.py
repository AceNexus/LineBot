import os
from flask import Flask
from .config import Config
from .logger import setup_logger
from .extensions import init_line_bot_api

def create_app():
    # 設定 Flask 應用
    app = Flask(__name__)

    # 將 Config 物件的設置加載到 Flask 應用配置
    app.config.from_object(Config)

    # 設定日誌級別
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    app.logger.setLevel(log_level)

    # 設置其他日誌格式等
    setup_logger(app)

    # 初始化 LINE Bot API
    init_line_bot_api(Config.LINE_CHANNEL_ACCESS_TOKEN, Config.LINE_CHANNEL_SECRET)
    
    # 初始化 API 藍圖
    from app.api import init_app
    init_app(app)

    return app