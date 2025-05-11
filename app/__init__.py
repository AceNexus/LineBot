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
    """創建並配置Flask應用程式"""
    app = Flask(__name__)

    # 加載配置
    profile = os.getenv("SPRING_PROFILES_ACTIVE", "local").lower()
    config = load_app_config(app, profile)
    print_config_info(app)

    # 設定日誌
    log_level = app.config.get("LOG_LEVEL", "INFO").upper()
    app.logger.setLevel(log_level)
    setup_logger(app)
    logger.info(f"Application started in {profile} environment with log level: {log_level}")

    # 註冊Eureka服務
    register_with_eureka(
        server_host=app.config.get("SERVER_HOST"),
        port=app.config.get("PORT"),
        eureka_host=app.config.get("EUREKA_SERVER_HOST"),
        eureka_port=app.config.get("EUREKA_SERVER_PORT"),
        profile=profile
    )

    # 初始化LINE Bot服務
    initialize_line_bot(app.config)

    # 初始化API路由
    init_app(app)
    logger.info("API routes initialized")

    # 初始化Groq服務
    initialize_groq_client(app.config.get("GROQ_API_KEY"))

    # 導入消息處理器
    from app.handlers.line_message_handlers import process_text_message
    logger.info("Message handlers loaded")

    return app


def register_with_eureka(server_host, port, eureka_host, eureka_port, profile):
    """註冊服務到Eureka服務發現系統"""

    # 檢查是否為本地環境
    is_local = profile.lower() == "local"

    # 本地環境不需要註冊 Eureka
    if is_local:
        logger.info("Running in local mode, skipping Eureka registration")
        return

    # 非本地環境必須提供完整的 Eureka 配置
    if not all([eureka_host, eureka_port]):
        logger.error("Eureka server configuration incomplete, application cannot start in non-local mode")
        exit(1)

    # 非本地環境必須提供服務本身的配置
    if not server_host or not port:
        logger.error("Service host or port not configured, application cannot start in non-local mode")
        exit(1)

    try:
        eureka_client.init(
            eureka_server=f"http://{eureka_host}:{eureka_port}/eureka/",
            app_name="linebotservice",
            instance_port=port,
            instance_ip=server_host,
        )
        logger.info(f"Successfully registered with Eureka server at {eureka_host}:{eureka_port}")
    except Exception as ex:
        logger.error(f"Failed to register with Eureka: {ex}")
        exit(1)


def initialize_line_bot(config):
    """初始化LINE Bot API客戶端"""
    channel_token = config.get("LINE_CHANNEL_ACCESS_TOKEN")
    channel_secret = config.get("LINE_CHANNEL_SECRET")

    if not channel_token or not channel_secret:
        logger.error("Missing LINE Bot credentials")
        exit(1)

    if not init_line_bot_api(channel_token, channel_secret):
        logger.error("Failed to initialize LINE Bot")
        exit(1)

    logger.info("LINE Bot initialized successfully")


def initialize_groq_client(api_key):
    """初始化Groq客戶端"""
    if not api_key:
        logger.warning("No GROQ_API_KEY provided, Groq service will be unavailable")
        return

    try:
        get_groq_client(api_key)
        logger.info("Groq client initialized successfully")
    except Exception as ex:
        logger.error(f"Failed to initialize Groq client: {ex}")
        exit(1)
