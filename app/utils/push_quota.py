import requests
from linebot.models import FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, SeparatorComponent

from app.config import Config
from app.utils.theme import COLOR_THEME


def get_line_push_quota():
    """查詢 LINE 官方推播總額度、已用額度、剩餘額度"""
    headers = {"Authorization": f"Bearer {Config.LINE_CHANNEL_ACCESS_TOKEN}"}

    try:
        # 查詢總額度
        quota_res = requests.get("https://api.line.me/v2/bot/message/quota", headers=headers, timeout=10)
        if quota_res.status_code != 200:
            return None, None, None, f"查詢失敗：{quota_res.status_code}"

        quota_data = quota_res.json()
        if quota_data.get("type") != "limited":
            return None, None, None, "此帳號無推播限制"

        total_quota = quota_data.get("value", 0)

        # 查詢已用額度
        usage_res = requests.get("https://api.line.me/v2/bot/message/quota/consumption", headers=headers, timeout=10)
        if usage_res.status_code != 200:
            return None, None, None, f"查詢使用量失敗：{usage_res.status_code}"

        usage_data = usage_res.json()
        used_quota = usage_data.get("totalUsage", 0)

        return total_quota, used_quota, total_quota - used_quota, None

    except Exception as e:
        return None, None, None, f"查詢失敗：{e}"


def get_line_push_quota_flex():
    total, used, remaining, error = get_line_push_quota()
    if error:
        return error
    return FlexSendMessage(
        alt_text="推播額度",
        contents=BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="LINE 推播額度",
                        weight="bold",
                        size="xl",
                        color=COLOR_THEME['text_primary'],
                        align="center",
                        margin="md"
                    ),
                    SeparatorComponent(margin="md", color=COLOR_THEME['separator']),
                    TextComponent(
                        text=f"總額度：{total}",
                        size="md",
                        color=COLOR_THEME['text_secondary'],
                        weight="bold",
                        margin="lg"
                    ),
                    TextComponent(
                        text=f"已用額度：{used}",
                        size="md",
                        color=COLOR_THEME['text_secondary'],
                        weight="bold",
                        margin="lg"
                    ),
                    TextComponent(
                        text=f"剩餘額度：{remaining}",
                        size="md",
                        color=COLOR_THEME['text_secondary'],
                        weight="bold",
                        margin="lg"
                    ),
                    TextComponent(
                        text="（每月 1 日重置）",
                        size="md",
                        color=COLOR_THEME['text_secondary'],
                        weight="bold",
                        margin="lg"
                    ),
                ],
                padding_all="lg",
                background_color=COLOR_THEME['card']
            )
        )
    )
