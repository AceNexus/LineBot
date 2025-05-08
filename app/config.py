import os

from dotenv import load_dotenv

# 載入 .env
load_dotenv()


class Config:
    PORT = int(os.getenv('PORT', 5000))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')


def load_config_from_spring_config(app_name, profile, config_server_url, username=None, password=None):
    import requests
    url = f"{config_server_url}/{app_name}/{profile}"
    auth = (username, password) if username and password else None

    response = requests.get(url, auth=auth)
    response.raise_for_status()

    config_data = response.json()
    config = {}
    for source in config_data.get("propertySources", []):
        config.update(source.get("source", {}))
    return config
