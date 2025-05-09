import logging
import os

import py_eureka_client.eureka_client as eureka_client
from flask import Flask

from app.api import init_app
from app.config import load_app_config
from app.config import print_config_info
from app.extensions import init_line_bot_api
from app.logger import setup_logger
from app.services.groq_service import get_groq_client

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)

    # 加載配置
    profile = os.getenv("SPRING_PROFILES_ACTIVE", "local").lower()
    config = load_app_config(app, profile)
    print_config_info(app)

    # 設定日誌
    log_level = config.get("LOG_LEVEL", "INFO").upper()
    app.logger.setLevel(log_level)
    setup_logger(app)

    # 註冊Eureka
    register_with_eureka(
        config.get("SERVER_HOST"),
        config.get("PORT"),
        config.get("EUREKA_SERVER_HOST"),
        config.get("EUREKA_SERVER_PORT"),
        is_local=(profile == "local")
    )

    # 初始化LINE Bot
    if not init_line_bot_api(config.get("LINE_CHANNEL_ACCESS_TOKEN"), config.get("LINE_CHANNEL_SECRET")):
        logger.error("Failed to initialize LINE Bot")
        exit(1)

    # 初始化API
    init_app(app)

    # 初始化 Groq
    get_groq_client(config.get("GROQ_API_KEY"))

    # 處理器
    from app.handlers.line_message_handlers import process_text_message

    return app


def register_with_eureka(server_host, port, eureka_host, eureka_port, is_local=False):
    # 如果沒有提供 Eureka 配置
    if not eureka_host or not eureka_port:
        logger.info("Skipping Eureka registration (server host or port not configured)")
        return

    try:
        eureka_client.init(
            eureka_server=f"http://{eureka_host}:{eureka_port}/eureka/",
            app_name="linebotservice",
            instance_port=instance_port,
            instance_ip=server_host,
        )
        logger.info(f"Successfully registered with Eureka server")
    except Exception as ex:
        if is_local:
            logger.warning(f"Failed to register with Eureka in local mode: {ex}")
        else:
            logger.error(f"Failed to register with Eureka: {ex}")
            exit(1)
