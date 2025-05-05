import logging

from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage

from app.extensions import line_bot_api, handler
from app.services import groq_service
from app.utils.lumos import get_lumos
from app.utils.menu import get_menu
from app.utils.movie import get_movies
from app.utils.news import get_news
from app.utils.words import get_english_word, get_japanese_word

logger = logging.getLogger(__name__)

# 用戶狀態追蹤字典
user_state = {}


@handler.add(MessageEvent, message=TextMessage)
def process_text_message(event):
    try:
        message_text = event.message.text
        user_id = event.source.user_id

        logger.info(f"Received text message from {user_id}: {message_text}")

        # 處理用戶輸入並獲取回應
        response_text = process_user_input(user_id, message_text)
        reply_to_user(event.reply_token, response_text)
    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        # 嘗試發送錯誤訊息給用戶
        try:
            reply_to_user(event.reply_token, "系統忙碌中，請稍後重試。若問題持續發生，請聯繫客服，謝謝您的耐心!")
        except Exception:
            logger.error("Failed to send error message to user")


def reply_to_user(reply_token, message):
    # 處理字串類型，轉為 TextSendMessage
    if isinstance(message, str):
        message = TextSendMessage(text=message)

    # 檢查是否為有效的訊息類型
    if not (isinstance(message, list) or isinstance(message, (TextSendMessage, FlexSendMessage))):
        raise TypeError("不支援的訊息類型，請使用字串、TextSendMessage、FlexSendMessage 或這些物件的列表")

    # 發送訊息
    line_bot_api.reply_message(reply_token, message)


# 檢查用戶輸入並回應
def process_user_input(user_id, message_text):
    msg = message_text.strip().lower()

    # 處理主選單命令
    if msg in ["0", "啊哇呾喀呾啦", "menu", "選單"]:
        # 清除任何可能的狀態
        user_state.pop(user_id, None)
        return get_menu()

    # 檢查用戶是否處於等待新聞數量的狀態
    if user_state.get(user_id) == "awaiting_news_count":
        if msg.isdigit():
            count = int(msg)
            if 1 <= count <= 10:  # 限制為 1-10 篇，與提示一致
                user_state.pop(user_id, None)  # 清除狀態
                return get_news(count)
            else:
                return "請輸入有效的數字（1～10）"
        else:
            # 如果用戶在等待數字時輸入了非數字內容
            if msg in ["路摸思", "lumos"]:
                # 清除狀態，處理新命令
                user_state.pop(user_id, None)
                # 繼續執行下面的命令處理邏輯
            else:
                return "請輸入數字 1～10 來選擇新聞數量，或輸入 0 返回主選單"

    # 處理主選單選項
    if msg == "1":
        user_state[user_id] = "awaiting_news_count"
        return "請輸入想查看的新聞數量（1～10）："
    elif msg == "2":
        return get_movies()
    elif msg == "3":
        return get_japanese_word()
    elif msg == "4":
        return get_english_word(user_id)
    elif msg in ["路摸思", "lumos"]:  # 哈利波特咒語的參考，顯示隱藏功能
        return get_lumos()
    else:
        # 清除狀態避免誤判
        user_state.pop(user_id, None)
        # 沒有符合條件的輸入，調用語言模型處理
        return groq_service.chat_with_groq(user_id, message_text)
