import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.utils.english_subscribe import SUBSCRIPTION_TIMES as ENGLISH_TIMES

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
    print(f"English subscription sent for {time_id}")


def send_japanese_notification(time_id):
    """發送日文訂閱通知"""
    print(f"Japanese subscription sent for {time_id}")
