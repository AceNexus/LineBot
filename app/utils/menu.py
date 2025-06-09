import logging

from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, ButtonComponent, PostbackAction,
    BubbleStyle, BlockStyle, SeparatorComponent
)

logger = logging.getLogger(__name__)


def get_menu():
    title = TextComponent(
        text="AI 功能選單",
        weight="bold",
        size="xl",
        align="center",
        color="#FFFFFF",
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇一項功能開始操作",
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
            SeparatorComponent(margin="lg", color="#666666")  # 更亮的分隔線
        ],
        spacing="md",
        padding_all="lg",
        background_color="#404040"
    )

    def create_button(emoji, label, action, color):
        return ButtonComponent(
            action=PostbackAction(
                label=f"{emoji} {label}",
                data=f"action={action}"
            ),
            style="primary",
            color=color,
            margin="sm",
            height="sm"
        )

    buttons = [
        create_button("📰", "新聞快訊", "news", "#FF7777"),  # 紅色
        create_button("🎬", "熱門電影", "movie", "#66E6E6"),  # 青色
        create_button("🇯🇵", "日文單字", "japanese", "#66B3FF"),  # 藍色
        create_button("🇺🇸", "英文單字", "english", "#A6D6A6"),  # 綠色
        create_button("📅", "英文訂閱", "english_subscribe", "#FFB366")  # 橙色
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

    return FlexSendMessage(alt_text="功能選單", contents=bubble)
