import logging
import os
from datetime import datetime

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import Config
from app.utils.english_subscribe import SUBSCRIPTION_TIMES as ENGLISH_TIMES, subscription_manager
from app.utils.english_words import get_english_words

logger = logging.getLogger(__name__)


def init_scheduler():
    """初始化排程器"""
    tz = os.environ.get('TZ', 'UTC')
    scheduler = BackgroundScheduler(timezone=tz)

    # 設定英文訂閱排程
    _setup_subscription_schedule(scheduler, ENGLISH_TIMES, 'english')

    # TODO 設定日文訂閱排程

    scheduler.start()
    logger.info("All language schedulers have been started")
    return scheduler


def _setup_subscription_schedule(scheduler, subscription_times, language):
    """設定特定語言的訂閱排程"""
    for time_id, time_str in subscription_times.items():
        try:
            hour, minute = map(int, time_str.split(':'))
            scheduler.add_job(
                func=send_subscription_notification,
                trigger=CronTrigger(hour=hour, minute=minute),
                args=[time_id, language],
                id=f'{language}_subscription_{time_id}',
                name=f'{language.title()} Schedule - {time_id}',
                replace_existing=True
            )
            logger.info(f"Successfully set {language} schedule {time_id}: Daily at {time_str}")
        except Exception as e:
            logger.error(f"Error setting up schedule for {language} {time_id}: {e}")


def send_subscription_notification(time_id, language):
    """發送訂閱通知"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Executing {language} {time_id} subscription notification - {current_time}")

    try:
        # 根據語言分發不同的通知邏輯
        if language == 'english':
            send_english_notification(time_id)
        elif language == 'japanese':
            send_japanese_notification(time_id)
        else:
            logger.warning(f"Unknown language type: {language}")
    except Exception as e:
        logger.error(f"Error in send_subscription_notification for {language} {time_id}: {e}")


def send_english_notification(time_id):
    """發送英文訂閱通知"""
    try:
        time_str = ENGLISH_TIMES.get(time_id)
        if not time_str:
            logger.error(f"Invalid time_id: {time_id}")
            return

        # 使用 subscription_manager 取得該時段的所有訂閱
        subscriptions = subscription_manager.get_subscriptions_by_time(time_str)

        if not subscriptions:
            logger.info(f"No subscriptions found for time slot: {time_str}")
            return

        logger.info(f"Found {len(subscriptions)} subscriptions for time slot: {time_str}")

        # 對每個訂閱者發送通知
        success_count = 0
        for subscription in subscriptions:
            try:
                logger.info(f"Processing subscription for user: {subscription.user_id}")
                logger.info(f"Difficulty ID: {subscription.difficulty_id}")
                logger.info(f"Difficulty Name: {subscription.difficulty_name}")
                logger.info(f"Word Count: {subscription.count}")

                # 獲取英文單字內容
                english_content = get_english_words(
                    chat_id=subscription.user_id,
                    difficulty_id=subscription.difficulty_id,
                    count=subscription.count
                )

                if english_content:
                    # 發送 LINE 訊息
                    send_line_message_push(
                        Config.LINE_CHANNEL_ACCESS_TOKEN,
                        subscription.user_id,
                        english_content
                    )
                    success_count += 1
                    logger.info(f"Successfully sent notification to user: {subscription.user_id}")
                else:
                    logger.warning(f"No content generated for user: {subscription.user_id}")

            except Exception as e:
                logger.error(f"Error sending notification to user {subscription.user_id}: {e}")
                continue

        logger.info(f"English notification batch completed. Success: {success_count}/{len(subscriptions)}")

    except Exception as e:
        logger.error(f"Error in send_english_notification: {e}")


def send_japanese_notification(time_id):
    """TODO 發送日文訂閱通知"""
    logger.info(f"Japanese subscription notification triggered for {time_id}")


def send_line_message_push(channel_token, user_id, message):
    """發送 LINE 推播訊息（支援文字與 Flex Message）"""
    if not channel_token or not message:
        logger.error("缺少 channel_token 或 message")
        return False

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {channel_token}'
    }

    def format_message(msg):
        if hasattr(msg, 'as_json_dict'):
            return msg.as_json_dict()
        if isinstance(msg, dict) and "type" in msg:
            return msg
        return {"type": "text", "text": str(msg)}

    # 單一或多筆訊息
    messages = [format_message(m) for m in message] if isinstance(message, list) else [format_message(message)]

    payload = {
        "to": user_id,
        "messages": messages
    }

    try:
        res = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers=headers,
            json=payload,
            timeout=30
        )
        if res.status_code == 200:
            logger.info(f"成功推播給使用者 {user_id}")
            return True
        else:
            logger.error(f"推播失敗：{res.status_code} - {res.text}")
            return False
    except Exception as e:
        logger.error(f"推播時發生錯誤：{e}")
        return False
