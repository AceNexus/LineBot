import logging

from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, ButtonComponent, PostbackAction,
    BubbleStyle, BlockStyle, SeparatorComponent
)

logger = logging.getLogger(__name__)


def get_subscription_menu() -> FlexSendMessage:
    """生成英文訂閱選單"""
    title = TextComponent(
        text="📚 英文單字訂閱",
        weight="bold",
        size="xl",
        align="center",
        color="#FFFFFF",
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇訂閱選項",
        size="sm",
        color="#E0E0E0",
        align="center",
        wrap=True,
        margin="sm"
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[
            title,
            subtitle,
            SeparatorComponent(margin="lg", color="#666666")
        ],
        spacing="md",
        padding_all="lg",
        background_color="#404040"
    )

    buttons = [
        ButtonComponent(
            action=PostbackAction(
                label="📖 設定訂閱",
                data="english_subscribe_setup"
            ),
            style="primary",
            color="#FFB366",
            margin="sm",
            height="sm"
        ),
        ButtonComponent(
            action=PostbackAction(
                label="📋 查閱訂閱",
                data="english_subscribe_view"
            ),
            style="primary",
            color="#FFB366",
            margin="sm",
            height="sm"
        ),
        ButtonComponent(
            action=PostbackAction(
                label="❌ 取消訂閱",
                data="english_subscribe_cancel"
            ),
            style="secondary",
            color="#FF7777",
            margin="sm",
            height="sm"
        )
    ]

    footer_box = BoxComponent(
        layout="vertical",
        contents=buttons,
        spacing="sm",
        padding_all="lg",
        background_color="#404040"
    )

    bubble = BubbleContainer(
        body=body_box,
        footer=footer_box,
        styles=BubbleStyle(
            body=BlockStyle(background_color="#404040"),
            footer=BlockStyle(background_color="#404040")
        )
    )

    return FlexSendMessage(alt_text="英文訂閱選單", contents=bubble)
