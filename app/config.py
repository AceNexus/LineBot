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
    if profile == "local":
        app.config.from_object(Config)
        logger.info("Running in local mode with local configuration")
        config = {key: value for key, value in app.config.items() if not key.startswith('_')}
    else:
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
                exit_with_error("Empty or invalid configuration returned from Spring Config Server")

            app.config.update(spring_config)
            print(f"Successfully loaded config from Spring Config Server for profile: {profile}")
            config = spring_config
        except Exception as ex:
            exit_with_error(f"Failed to load config from Spring Config Server ({profile}): {ex}")

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
        raise Exception(f"Network error connecting to Config Server: {e}")
    except ValueError as e:
        raise Exception(f"Configuration error: {e}")


def exit_with_error(message):
    logger.error(f"FATAL ERROR: {message}")
    exit(1)


def print_config_info(app):
    print("--- Start Effective Config values ---")
    for key, value in app.config.items():
        if not key.startswith("_"):
            print(f"  {key}: {value}")
    print("--- End Effective Config values ---")
