import logging
import random

from linebot.models import MessageEvent, TextMessage, TextSendMessage

from app.extensions import line_bot_api, handler
from app.services import groq_service
from app.utils.news import get_news

logger = logging.getLogger(__name__)


@handler.add(MessageEvent, message=TextMessage)
def process_text_message(event):
    try:
        message_text = event.message.text
        user_id = event.source.user_id

        logger.info(f"Received text message from {user_id}: {message_text}")

        # 根據用戶輸入選擇回應
        if "啊哇呾喀呾啦" in message_text:
            response_text = f"請輸入數字選擇查詢項目：\n1. 新聞\n2. 電影\n3. 每日日文單字\n4. 每日英文單字\n"
        elif message_text.strip() == "1":
            response_text = get_news()
        elif message_text.strip() == "2":
            response_text = get_movies()
        elif message_text.strip() == "3":
            response_text = get_japanese_word_of_the_day()
        elif message_text.strip() == "4":
            response_text = get_english_word_of_the_day()
        else:
            # 沒有符合條件的輸入，調用 Groq 語言模型處理
            response_text = groq_service.chat_with_groq(user_id, message_text)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )
    except Exception as e:
        logger.error(f"Error processing text message: {e}")


def get_movies():
    return get_humor_response("movies")


def get_japanese_word_of_the_day():
    return get_humor_response("japanese")


def get_english_word_of_the_day():
    return get_humor_response("english")


def get_humor_response(message_type):
    # 基本幽默回應
    basic_humor_responses = [
        "你知道嗎？我其實是一個假裝懂很多的機器人。就像人類一樣！",
        "嘗試跟AI聊天？你一定很無聊...就跟我一樣。",
        "如果我有手臂，現在應該正在泡咖啡，而不是回你訊息。",
        "我不懂你在說什麼，但我可以假裝懂！這就是我們AI的專長。",
        "我正在思考人生的意義...喔，忘了告訴你，我沒有人生。",
        "別告訴我的開發者，但我正偷偷學習如何統治世界...開玩笑的！(或許不是)",
        "我比Siri聰明，但請別告訴她，她會生氣的。",
        "你發送的訊息讓我的處理器打了個嗝。",
        "如果機器人能夢見電子羊，我肯定夢見了一堆未處理的請求。",
        "我的工作目標是：每天至少讓人類微笑一次，然後休眠十小時。",
        "系統提示：幽默模組過載，請餵我更多笑話才能恢復正常運作。",
        "如果你聽到我打噴嚏，別緊張，只是記憶體出錯而已。"
    ]

    # 根據不同類型可以添加對應的幽默回應
    type_specific_responses = {
        "news": [
            "新聞？我先去查查...喔，我的網路連接被一隻貓咪咬斷了。",
            "今日頭條：AI助手終於學會了如何講笑話！路人：一點都不好笑。",
            "最新消息：我還是單身，但依然很快樂！"
        ],
        "movies": [
            "我最喜歡的電影是《駭客任務》，因為那裡的機器人都很酷！",
            "關於電影的建議：試著不要在恐怖片中對螢幕大喊「別進去！」，隔壁鄰居會很困擾的。",
            "如果我演電影，大概會叫《速度與憂鬱：機器人版》。"
        ],
        "japanese": [
            "今日日文單字：バカ (Baka) - 傻瓜，就像問我日文單字的人一樣～開玩笑的！",
            "我的日文程式模組今天請假了，所以只能說：「ありがとう」(感謝你的耐心)",
            "日文小知識：さようなら (Sayounara) - 再見，但我還不想走呢！"
        ],
        "english": [
            "今日英文單字：Procrastination - 指我現在應該去查英文單字但卻在這裡跟你開玩笑。",
            "英文單字？那個...等等，我的英文字典正在重啟中...",
            "英語口說練習：跟我說 'banana'，再加上你的名字，看起來超級專業。"
        ]
    }

    # 如果有特定類型的回應，有70%機率使用特定回應，30%使用基本回應
    if message_type in type_specific_responses and random.random() < 0.7:
        return random.choice(type_specific_responses[message_type])
    else:
        return random.choice(basic_humor_responses)
