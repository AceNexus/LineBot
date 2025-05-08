import logging
import os

from flask import Flask

from app.api import init_app
from app.config import Config, load_config_from_spring_config
from app.extensions import init_line_bot_api
from app.logger import setup_logger

logger = logging.getLogger(__name__)


def create_app():
    # 初始化 Flask 應用
    app = Flask(__name__)

    # 初始化 .env 設定
    app.config.from_object(Config)

    # 根據 SPRING_PROFILE 判斷是否載入 Spring Config
    profile = os.getenv("SPRING_PROFILE", "local").lower()
    line_channel_access_token = app.config.get("LINE_CHANNEL_ACCESS_TOKEN")
    line_channel_secret = app.config.get("LINE_CHANNEL_SECRET")
    groq_api_key = os.getenv('GROQ_API_KEY')

    # 如果是 dev 或 prod 環境，嘗試從 Spring Config Server 加載配置
    if profile in ["dev", "prod"]:
        try:
            config_server_url = os.getenv("SPRING_CONFIG_URL")
            config_server_user = os.getenv("SPRING_CONFIG_USERNAME")
            config_server_pass = os.getenv("SPRING_CONFIG_PASSWORD")

            # 嘗試從 Spring Config Server 加載配置
            spring_config = load_config_from_spring_config(
                "linebotservice", profile, config_server_url,
                username=config_server_user, password=config_server_pass
            )

            # 檢查配置是否為空
            if spring_config and isinstance(spring_config, dict) and spring_config:
                app.config.update(spring_config)
                line_channel_access_token = spring_config.get("LINE_CHANNEL_ACCESS_TOKEN")
                line_channel_secret = spring_config.get("LINE_CHANNEL_SECRET")
                groq_api_key = spring_config.get("GROQ_API_KEY")
                logger.info(f"Loaded config from Spring Config Server for profile: {profile}")
            else:
                logger.error("Failed to initialize Spring Config Server. Exiting...")
                exit(1)
        except Exception as ex:
            logger.warning(f"Failed to load config from Spring Config Server ({profile}): {ex}")
            exit(1)

    # 設定日誌
    log_level = app.config.get('LOG_LEVEL', 'INFO').upper()
    app.logger.setLevel(log_level)
    setup_logger(app)

    # 初始化 LINE Bot
    if not init_line_bot_api(line_channel_access_token, line_channel_secret):
        logger.error("Failed to initialize LINE Bot. Exiting...")
        exit(1)

    # 初始化 API
    init_app(app)

    # 處理器
    from app.handlers.line_message_handlers import process_text_message

    return app
