import logging
from typing import List, Dict, Tuple

from linebot.models import (
    ButtonComponent, PostbackAction,
    BubbleStyle, BlockStyle
)
from linebot.models import FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, SeparatorComponent

from app.models.subscription import Subscription, SubscriptionManager
from app.utils.english_words import DIFFICULTY_NAMES
from app.utils.theme import (
    COLOR_THEME
)

logger = logging.getLogger(__name__)

# 訂閱時段
SUBSCRIPTION_TIMES = {
    '1': '09:00',
    '2': '12:00',
    '3': '15:00',
    '4': '18:00',
    '5': '21:00'
}

# 建立訂閱管理器實例
subscription_manager = SubscriptionManager()


def save_subscription(user_id: str, difficulty_id: str, count: int, time_id: str) -> bool:
    """
    儲存單一時段的訂閱設定

    Args:
        user_id: 使用者ID
        difficulty_id: 難度ID
        count: 單字數量
        time_id: 時段ID

    Returns:
        bool: 儲存是否成功
    """
    try:
        time = SUBSCRIPTION_TIMES.get(time_id, '00:00')
        subscription = Subscription(
            user_id=user_id,
            difficulty_id=difficulty_id,
            difficulty_name=DIFFICULTY_NAMES.get(difficulty_id, '未知難度'),
            count=count,
            time=time
        )
        subscription_manager.add_subscription(subscription)
        logger.info(f"Successfully saved subscription for user {user_id} - time slot: {time}")
        return True
    except Exception as e:
        logger.error(f"Failed to save subscription - user: {user_id}, time_id: {time_id}, error: {e}")
        return False


def get_user_subscriptions(user_id: str) -> List[Subscription]:
    """獲取使用者的訂閱設定"""
    return subscription_manager.get_user_subscriptions(user_id)


def cancel_user_subscriptions(user_id: str) -> bool:
    """
    取消使用者的所有訂閱

    Args:
        user_id: 使用者ID

    Returns:
        bool: 取消是否成功
    """
    try:
        subscription_manager.remove_user_subscriptions(user_id)
        logger.info(f"Successfully canceled all subscriptions for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to cancel subscriptions - user: {user_id}, error: {e}")
        return False


def parse_subscription_data(data_string: str) -> Tuple[str, int, str]:
    """
    解析訂閱資料字串

    Args:
        data_string: 格式為 "difficulty_id/count/time_id"

    Returns:
        tuple: (difficulty_id, count, time_id)
    """
    parts = data_string.split('/')
    difficulty_id = parts[0]
    count = int(parts[1])
    time_id = parts[2] if len(parts) > 2 else '1'
    return difficulty_id, count, time_id


def handle_subscription_time(data: dict) -> Tuple[str, int, str]:
    """處理訂閱時段選擇"""
    data_string = data['english_subscribe_time'][0]
    difficulty_id, count, time_id = parse_subscription_data(data_string)
    return difficulty_id, count, time_id


def handle_subscription_save(data: Dict, user_id: str) -> FlexSendMessage:
    """處理訂閱儲存"""
    try:
        data_string = data['english_subscribe_save'][0]
        difficulty_id, count, time_id = parse_subscription_data(data_string)

        if save_subscription(user_id, difficulty_id, count, time_id):
            time_name = SUBSCRIPTION_TIMES.get(time_id, '未知時段')
            difficulty_name = DIFFICULTY_NAMES.get(difficulty_id, '未知難度')

            # 成功訂閱的 Flex Message
            success_bubble = BubbleContainer(
                body=BoxComponent(
                    layout="vertical",
                    contents=[
                        TextComponent(
                            text="訂閱成功！",
                            weight="bold",
                            size="xl",
                            color=COLOR_THEME['text_primary'],
                            align="center"
                        ),
                        SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                        BoxComponent(
                            layout="vertical",
                            margin="lg",
                            spacing="md",
                            contents=[
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(text="📚", size="lg", flex=1),
                                        TextComponent(text="難度", size="md", color=COLOR_THEME['text_hint'], flex=2),
                                        TextComponent(text=difficulty_name, size="md", weight="bold",
                                                      color=COLOR_THEME['text_primary'], flex=4, align="end")
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(text="📊", size="lg", flex=1),
                                        TextComponent(text="數量", size="md", color=COLOR_THEME['text_hint'], flex=2),
                                        TextComponent(text=f"{count} 個單字", size="md", weight="bold",
                                                      color=COLOR_THEME['text_primary'], flex=4, align="end")
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(text="⏰", size="lg", flex=1),
                                        TextComponent(text="時間", size="md", color=COLOR_THEME['text_hint'], flex=2),
                                        TextComponent(text=time_name, size="md", weight="bold",
                                                      color=COLOR_THEME['text_primary'], flex=4, align="end")
                                    ]
                                )
                            ]
                        ),
                        SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                        TextComponent(
                            text="每日準時為您推送英文單字！",
                            size="sm",
                            color=COLOR_THEME['text_secondary'],
                            align="center",
                            margin="lg"
                        )
                    ],
                    padding_all="lg",
                    background_color=COLOR_THEME['primary']
                ),
                styles=BubbleStyle(
                    body=BlockStyle(background_color=COLOR_THEME['primary'])
                )
            )
            return FlexSendMessage(alt_text="訂閱成功", contents=success_bubble)
        else:
            # 失敗的 Flex Message
            error_bubble = BubbleContainer(
                body=BoxComponent(
                    layout="vertical",
                    contents=[
                        TextComponent(
                            text="❌ 訂閱失敗",
                            weight="bold",
                            size="xl",
                            color=COLOR_THEME['text_primary'],
                            align="center"
                        ),
                        SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                        TextComponent(
                            text="系統暫時無法處理您的訂閱請求\n請稍後再試",
                            size="md",
                            color=COLOR_THEME['text_secondary'],
                            align="center",
                            wrap=True,
                            margin="lg"
                        )
                    ],
                    padding_all="lg",
                    background_color=COLOR_THEME['error']
                ),
                styles=BubbleStyle(
                    body=BlockStyle(background_color=COLOR_THEME['error'])
                )
            )
            return FlexSendMessage(alt_text="訂閱失敗", contents=error_bubble)

    except Exception as e:
        logger.error(f"Failed to handle subscription save: {e}")
        # 系統錯誤的 Flex Message
        error_bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="⚠️ 系統錯誤",
                        weight="bold",
                        size="xl",
                        color=COLOR_THEME['text_primary'],
                        align="center"
                    ),
                    SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                    TextComponent(
                        text="系統發生未預期的錯誤\n請稍後再試或聯絡客服",
                        size="md",
                        color=COLOR_THEME['text_secondary'],
                        align="center",
                        wrap=True,
                        margin="lg"
                    )
                ],
                padding_all="lg",
                background_color=COLOR_THEME['warning']
            ),
            styles=BubbleStyle(
                body=BlockStyle(background_color=COLOR_THEME['warning'])
            )
        )
        return FlexSendMessage(alt_text="系統錯誤", contents=error_bubble)


def handle_subscription_view(user_id: str) -> FlexSendMessage:
    """處理訂閱查詢"""
    subscriptions = get_user_subscriptions(user_id)

    if not subscriptions:
        # 沒有訂閱的 Flex Message
        no_subscription_bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="📋 訂閱查詢",
                        weight="bold",
                        size="xl",
                        color=COLOR_THEME['text_primary'],
                        align="center"
                    ),
                    SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                    TextComponent(
                        text="❗ 您目前沒有任何訂閱",
                        size="lg",
                        color=COLOR_THEME['text_secondary'],
                        align="center",
                        margin="lg"
                    ),
                    TextComponent(
                        text="點選「設定訂閱」開始您的英文學習之旅！",
                        size="sm",
                        color=COLOR_THEME['text_hint'],
                        align="center",
                        wrap=True,
                        margin="md"
                    )
                ],
                padding_all="lg",
                background_color=COLOR_THEME['neutral']
            ),
            styles=BubbleStyle(
                body=BlockStyle(background_color=COLOR_THEME['neutral'])
            )
        )
        return FlexSendMessage(alt_text="訂閱查詢", contents=no_subscription_bubble)

    # 建立訂閱列表內容
    contents = [
        TextComponent(
            text="📋 您的訂閱設定",
            weight="bold",
            size="xl",
            color=COLOR_THEME['text_primary'],
            align="center"
        ),
        SeparatorComponent(margin="lg", color=COLOR_THEME['separator'])
    ]

    for i, sub in enumerate(subscriptions, 1):
        subscription_info = BoxComponent(
            layout="vertical",
            margin="lg",
            spacing="sm",
            contents=[
                TextComponent(text=f"📌 訂閱 {i}", weight="bold", size="md", color=COLOR_THEME['success']),
                BoxComponent(
                    layout="horizontal",
                    contents=[
                        TextComponent(text="📚", size="md", flex=1),
                        TextComponent(text="難度", size="sm", color=COLOR_THEME['text_hint'], flex=2),
                        TextComponent(text=sub.difficulty_name, size="sm", weight="bold",
                                      color=COLOR_THEME['text_primary'], flex=4, align="end")
                    ]
                ),
                BoxComponent(
                    layout="horizontal",
                    contents=[
                        TextComponent(text="📊", size="md", flex=1),
                        TextComponent(text="數量", size="sm", color=COLOR_THEME['text_hint'], flex=2),
                        TextComponent(text=f"{sub.count} 個單字", size="sm", weight="bold",
                                      color=COLOR_THEME['text_primary'], flex=4, align="end")
                    ]
                ),
                BoxComponent(
                    layout="horizontal",
                    contents=[
                        TextComponent(text="⏰", size="md", flex=1),
                        TextComponent(text="時間", size="sm", color=COLOR_THEME['text_hint'], flex=2),
                        TextComponent(text=sub.time, size="sm", weight="bold",
                                      color=COLOR_THEME['text_primary'], flex=4, align="end")
                    ]
                )
            ]
        )
        contents.append(subscription_info)

        if i < len(subscriptions):
            contents.append(SeparatorComponent(margin="md", color=COLOR_THEME['separator']))

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=contents,
            padding_all="lg",
            background_color=COLOR_THEME['card']
        ),
        styles=BubbleStyle(
            body=BlockStyle(background_color=COLOR_THEME['card'])
        )
    )

    return FlexSendMessage(alt_text="訂閱查詢", contents=bubble)


def handle_subscription_cancel(user_id: str) -> FlexSendMessage:
    """
    處理訂閱取消

    Args:
        user_id: 使用者ID

    Returns:
        FlexSendMessage: 取消結果訊息
    """
    # 檢查是否有訂閱
    subscriptions = get_user_subscriptions(user_id)

    if not subscriptions:
        # 沒有訂閱可取消的 Flex Message
        no_subscription_bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="取消訂閱",
                        weight="bold",
                        size="xl",
                        color=COLOR_THEME['text_primary'],
                        align="center"
                    ),
                    SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                    TextComponent(
                        text="❗ 您目前沒有任何訂閱",
                        size="lg",
                        color=COLOR_THEME['text_secondary'],
                        align="center",
                        margin="lg"
                    ),
                    TextComponent(
                        text="沒有需要取消的訂閱項目",
                        size="sm",
                        color=COLOR_THEME['text_hint'],
                        align="center",
                        margin="md"
                    )
                ],
                padding_all="lg",
                background_color=COLOR_THEME['neutral']
            ),
            styles=BubbleStyle(
                body=BlockStyle(background_color=COLOR_THEME['neutral'])
            )
        )
        return FlexSendMessage(alt_text="取消訂閱", contents=no_subscription_bubble)

    # 取消訂閱
    if cancel_user_subscriptions(user_id):
        # 成功取消訂閱的 Flex Message
        success_bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="取消成功！",
                        weight="bold",
                        size="xl",
                        color=COLOR_THEME['text_primary'],
                        align="center"
                    ),
                    SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                    TextComponent(
                        text="✅ 已成功取消所有訂閱！",
                        size="lg",
                        color=COLOR_THEME['text_secondary'],
                        align="center",
                        margin="lg"
                    ),
                    BoxComponent(
                        layout="vertical",
                        margin="lg",
                        spacing="sm",
                        contents=[
                            TextComponent(
                                text="📚 所有英文單字推送已停止",
                                size="sm",
                                color=COLOR_THEME['text_hint'],
                                align="center"
                            ),
                            TextComponent(
                                text="如需重新訂閱，請點選「設定訂閱」",
                                size="sm",
                                color=COLOR_THEME['text_hint'],
                                align="center"
                            )
                        ]
                    )
                ],
                padding_all="lg",
                background_color=COLOR_THEME['success']
            ),
            styles=BubbleStyle(
                body=BlockStyle(background_color=COLOR_THEME['success'])
            )
        )
        return FlexSendMessage(alt_text="取消訂閱成功", contents=success_bubble)
    else:
        # 取消失敗的 Flex Message
        error_bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="❌ 取消失敗",
                        weight="bold",
                        size="xl",
                        color=COLOR_THEME['text_primary'],
                        align="center"
                    ),
                    SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                    TextComponent(
                        text="系統暫時無法處理取消請求\n請稍後再試",
                        size="md",
                        color=COLOR_THEME['text_secondary'],
                        align="center",
                        wrap=True,
                        margin="lg"
                    )
                ],
                padding_all="lg",
                background_color=COLOR_THEME['error']
            ),
            styles=BubbleStyle(
                body=BlockStyle(background_color=COLOR_THEME['error'])
            )
        )
        return FlexSendMessage(alt_text="取消訂閱失敗", contents=error_bubble)


def create_menu_bubble(title: str, subtitle: str, buttons: List[ButtonComponent]) -> BubbleContainer:
    """建立選單泡泡"""
    title_component = TextComponent(
        text=title,
        weight="bold",
        size="xl",
        align="center",
        color=COLOR_THEME['text_primary'],
        wrap=True
    )

    subtitle_component = TextComponent(
        text=subtitle,
        size="sm",
        color=COLOR_THEME['text_secondary'],
        align="center",
        wrap=True,
        margin="sm"
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[
            title_component,
            subtitle_component,
            SeparatorComponent(margin="lg", color=COLOR_THEME['separator'])
        ],
        spacing="md",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    footer_box = BoxComponent(
        layout="vertical",
        contents=buttons,
        spacing="sm",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    return BubbleContainer(
        body=body_box,
        footer=footer_box,
        styles=BubbleStyle(
            body=BlockStyle(background_color=COLOR_THEME['card']),
            footer=BlockStyle(background_color=COLOR_THEME['card'])
        )
    )


def get_subscription_menu() -> FlexSendMessage:
    """生成英文訂閱選單"""
    buttons = [
        ButtonComponent(
            action=PostbackAction(
                label="📖 設定訂閱",
                data="action=english_subscribe_setup"
            ),
            style="primary",
            color=COLOR_THEME['primary'],
            margin="sm",
            height="sm"
        ),
        ButtonComponent(
            action=PostbackAction(
                label="📋 查閱訂閱",
                data="action=english_subscribe_view"
            ),
            style="primary",
            color=COLOR_THEME['info'],
            margin="sm",
            height="sm"
        ),
        ButtonComponent(
            action=PostbackAction(
                label="❌ 取消訂閱",
                data="action=english_subscribe_cancel"
            ),
            style="secondary",
            color=COLOR_THEME['error'],
            margin="sm",
            height="sm"
        )
    ]

    bubble = create_menu_bubble("📚 英文單字訂閱", "請選擇訂閱選項", buttons)
    return FlexSendMessage(alt_text="英文訂閱選單", contents=bubble)


def get_difficulty_menu() -> FlexSendMessage:
    """生成訂閱難度選單"""
    buttons = []
    for level_id, level_name in DIFFICULTY_NAMES.items():
        button = ButtonComponent(
            action=PostbackAction(
                label=f"📖 {level_name}",
                data=f"english_subscribe_difficulty={level_id}"
            ),
            style="primary",
            color=COLOR_THEME['primary'],
            margin="sm",
            height="sm"
        )
        buttons.append(button)

    bubble = create_menu_bubble("📚 選擇單字難度", "請選擇訂閱的單字難度等級", buttons)
    return FlexSendMessage(alt_text="訂閱難度選單", contents=bubble)


def get_count_menu(difficulty_id: str) -> FlexSendMessage:
    """生成訂閱數量選單"""
    difficulty_name = DIFFICULTY_NAMES.get(difficulty_id, "英文單字")

    buttons = []
    for count in range(1, 6):
        button = ButtonComponent(
            action=PostbackAction(
                label=f"📖 {count} 個單字",
                data=f"english_subscribe_count={difficulty_id}/{count}"
            ),
            style="primary",
            color=COLOR_THEME['primary'],
            margin="sm",
            height="sm"
        )
        buttons.append(button)

    bubble = create_menu_bubble(f"📚 {difficulty_name}", "請選擇每次發送的單字數量", buttons)
    return FlexSendMessage(alt_text="訂閱數量選單", contents=bubble)


def get_time_menu(difficulty_id: str, count: int) -> FlexSendMessage:
    """生成訂閱時間選單"""
    buttons = []
    for time_id, time_name in SUBSCRIPTION_TIMES.items():
        button = ButtonComponent(
            action=PostbackAction(
                label=f"⏰ {time_name}",
                data=f"english_subscribe_time={difficulty_id}/{count}/{time_id}"
            ),
            style="primary",
            color=COLOR_THEME['primary'],
            margin="sm",
            height="sm"
        )
        buttons.append(button)

    bubble = create_menu_bubble("⏰ 選擇訂閱時間", "請選擇接收單字的時間", buttons)
    return FlexSendMessage(alt_text="訂閱時間選單", contents=bubble)


def get_subscription_confirm(difficulty_id: str, count: int, selected_time: str) -> FlexSendMessage:
    """生成訂閱確認訊息"""
    difficulty_name = DIFFICULTY_NAMES.get(difficulty_id, "未知難度")
    time_name = SUBSCRIPTION_TIMES.get(selected_time, "未知時段")

    title = TextComponent(
        text="📚 確認訂閱",
        weight="bold",
        size="xl",
        align="center",
        color=COLOR_THEME['text_primary']
    )

    content = TextComponent(
        text="您將訂閱以下內容：",
        size="md",
        color=COLOR_THEME['text_secondary'],
        align="center",
        margin="lg"
    )

    # 訂閱詳情
    detail_contents = [
        BoxComponent(
            layout="horizontal",
            contents=[
                TextComponent(text="📚", size="lg", flex=1),
                TextComponent(text="難度", size="md", color=COLOR_THEME['text_hint'], flex=2),
                TextComponent(text=difficulty_name, size="md", weight="bold",
                              color=COLOR_THEME['text_primary'], flex=4, align="end")
            ]
        ),
        BoxComponent(
            layout="horizontal",
            contents=[
                TextComponent(text="📊", size="lg", flex=1),
                TextComponent(text="數量", size="md", color=COLOR_THEME['text_hint'], flex=2),
                TextComponent(text=f"{count} 個單字", size="md", weight="bold",
                              color=COLOR_THEME['text_primary'], flex=4, align="end")
            ]
        ),
        BoxComponent(
            layout="horizontal",
            contents=[
                TextComponent(text="⏰", size="lg", flex=1),
                TextComponent(text="時段", size="md", color=COLOR_THEME['text_hint'], flex=2),
                TextComponent(text=time_name, size="md", weight="bold",
                              color=COLOR_THEME['text_primary'], flex=4, align="end")
            ]
        )
    ]

    confirm_text = TextComponent(
        text="確認要訂閱嗎？",
        size="md",
        color=COLOR_THEME['text_secondary'],
        align="center",
        margin="lg"
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[
            title,
            SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
            content,
            BoxComponent(
                layout="vertical",
                margin="lg",
                spacing="md",
                contents=detail_contents
            ),
            SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
            confirm_text
        ],
        spacing="md",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    confirm_button = ButtonComponent(
        action=PostbackAction(
            label="✅ 確認訂閱",
            data=f"english_subscribe_save={difficulty_id}/{count}/{selected_time}"
        ),
        style="primary",
        color=COLOR_THEME['success'],
        margin="sm",
        height="sm"
    )

    footer_box = BoxComponent(
        layout="vertical",
        contents=[confirm_button],
        spacing="sm",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    bubble = BubbleContainer(
        body=body_box,
        footer=footer_box,
        styles=BubbleStyle(
            body=BlockStyle(background_color=COLOR_THEME['card']),
            footer=BlockStyle(background_color=COLOR_THEME['card'])
        )
    )

    return FlexSendMessage(alt_text="訂閱確認", contents=bubble)
