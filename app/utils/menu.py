import logging

from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, ButtonComponent, MessageAction, SeparatorComponent,
    BubbleStyle, BlockStyle
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

    def create_button(emoji, label, text, color):
        return ButtonComponent(
            action=MessageAction(label=f"{emoji} {label}", text=text),
            style="primary",
            color=color,
            margin="sm",
            height="sm"
        )

    buttons = [
        create_button("📰", "新聞快訊", "1", "#FF7777"),  # 紅色
        create_button("🎬", "熱門電影", "2", "#66E6E6"),  # 青色
        create_button("🇯🇵", "日文單字", "3", "#66B3FF"),  # 藍色
        create_button("🇺🇸", "英文單字", "4", "#A6D6A6")   # 綠色
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