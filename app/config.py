import os

from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


class Config:
    PORT = int(os.getenv('PORT', 5000))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
