import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.utils.english_subscribe import SUBSCRIPTION_TIMES as ENGLISH_TIMES, subscription_manager

logger = logging.getLogger(__name__)


def init_scheduler():
    """初始化排程器"""
    scheduler = BackgroundScheduler()

    # 設定英文訂閱排程
    _setup_subscription_schedule(scheduler, ENGLISH_TIMES, 'english')

    # TODO 設定日文訂閱排程

    scheduler.start()
    logger.info("All language schedulers have been started")
    return scheduler


def _setup_subscription_schedule(scheduler, subscription_times, language):
    """設定特定語言的訂閱排程"""
    for time_id, time_str in subscription_times.items():
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


def send_subscription_notification(time_id, language):
    """發送訂閱通知"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Executing {language} {time_id} subscription notification - {current_time}")

    # 根據語言分發不同的通知邏輯
    if language == 'english':
        send_english_notification(time_id)
    elif language == 'japanese':
        send_japanese_notification(time_id)
    else:
        logger.warning(f"Unknown language type: {language}")


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

        # 對每個訂閱者發送通知
        for subscription in subscriptions:
            try:
                # 取得訂閱者的資訊
                logger.info(f"Start - Successfully sent notification to user")
                logger.info(subscription.user_id)
                logger.info(subscription.difficulty_id)
                logger.info(subscription.difficulty_name)
                logger.info(subscription.count)
                logger.info(f"End - Successfully sent notification to user")

            except Exception as e:
                logger.error(f"Error sending notification to user {subscription.user_id}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error in send_english_notification: {e}")


def send_japanese_notification(time_id):
    """發送日文訂閱通知"""
    print(f"Japanese subscription sent for {time_id}")
