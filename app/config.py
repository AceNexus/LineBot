import logging
import os

import requests
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    SERVER_HOST = os.getenv('SERVER_HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', 5000))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    SPRING_CONFIG_URL = os.getenv('SPRING_CONFIG_URL')
    SPRING_CONFIG_USERNAME = os.getenv('SPRING_CONFIG_USERNAME')
    SPRING_CONFIG_PASSWORD = os.getenv('SPRING_CONFIG_PASSWORD')
    EUREKA_SERVER_HOST = os.getenv('EUREKA_SERVER_HOST')
    EUREKA_SERVER_PORT = os.getenv('EUREKA_SERVER_PORT')


def load_app_config(app, profile):
    print("Loading config for profile:", profile)

    # 先從 .env 配置載入
    app.config.from_object(Config)
    logger.info(f"Running in {profile} mode with .env configuration")

    # 如果是非 local 模式，則從 Spring Config Server 加載配置
    if profile != "local":
        spring_config_url = os.getenv("SPRING_CONFIG_URL")
        spring_config_username = os.getenv("SPRING_CONFIG_USERNAME")
        spring_config_password = os.getenv("SPRING_CONFIG_PASSWORD")

        try:
            logger.info(f"Attempting to load config from Spring Config Server for profile: {profile}")
            spring_config = load_config_from_spring_config(
                "linebotservice", profile, spring_config_url,
                username=spring_config_username, password=spring_config_password
            )
            if not spring_config:
                logger.warning("Empty configuration returned from Spring Config Server, using defaults or .env values")

            # 更新配置：只更新已定義的自定義配置項
            for key in spring_config:
                if key in Config.__dict__ and not key.startswith("_"):
                    app.config[key] = spring_config[key]

            print(f"Successfully loaded config from Spring Config Server for profile: {profile}")
            config = spring_config
        except Exception as ex:
            exit_with_error(f"Failed to load config from Spring Config Server ({profile}): {ex}")
    else:
        config = {key: value for key, value in app.config.items() if not key.startswith('_')}

    return config


def load_config_from_spring_config(app_name, profile, config_server_url, username=None, password=None):
    if not config_server_url:
        raise ValueError("Spring Config Server URL not provided")

    url = f"{config_server_url}/{app_name}/{profile}"
    auth = (username, password) if username and password else None

    try:
        response = requests.get(url, auth=auth, timeout=10)
        response.raise_for_status()
        config_data = response.json()

        if "propertySources" not in config_data:
            raise ValueError("Invalid configuration format received from server")

        raw_config = {}
        for source in config_data["propertySources"]:
            raw_config.update(source.get("source", {}))

        def normalize_key(key):
            return key.upper().replace(".", "_")

        config = {}
        for k, v in raw_config.items():
            norm_key = normalize_key(k)
            if isinstance(v, str):
                if v.lower() in ('true', 'false'):
                    config[norm_key] = v.lower() == 'true'
                elif v.isdigit():
                    config[norm_key] = int(v)
                else:
                    config[norm_key] = v
            else:
                config[norm_key] = v

        return config

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error connecting to Config Server: {e}")
        raise Exception(f"Network error connecting to Config Server: {e}")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise Exception(f"Configuration error: {e}")


def exit_with_error(message):
    logger.error(f"FATAL ERROR: {message}")
    exit(1)


def print_config_info(app):
    print("-" * 60)

    custom_keys = [attr for attr in dir(Config) if not attr.startswith("_") and attr.isupper()]
    for key in custom_keys:
        value = app.config.get(key)
        if value is not None:
            print(f"{key:<30} : {value}")

    print("-" * 60)
