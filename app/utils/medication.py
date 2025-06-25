import logging

from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, BubbleStyle, BlockStyle, SeparatorComponent
)

from app.utils.menu import create_button
from app.utils.theme import COLOR_THEME

logger = logging.getLogger(__name__)


def get_medication_menu():
    title = TextComponent(
        text="用藥管理",
        weight="bold",
        size="xl",
        align="center",
        color=COLOR_THEME['text_primary'],
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇用藥功能",
        size="sm",
        color=COLOR_THEME['text_secondary'],
        align="center",
        wrap=True,
        margin="sm"
    )

    buttons = [
        create_button("藥品管理", "med_reminder_setting", COLOR_THEME['primary']),
        create_button("提醒功能", "med_report", COLOR_THEME['info']),
        create_button("查看記錄", "med_history", COLOR_THEME['primary'])
    ]

    footer_box = BoxComponent(
        layout="vertical",
        contents=buttons,
        spacing="sm",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=[title, subtitle, SeparatorComponent(margin="lg", color=COLOR_THEME['separator'])],
            spacing="md",
            padding_all="lg",
            background_color=COLOR_THEME['card']
        ),
        footer=footer_box,
        styles=BubbleStyle(
            body=BlockStyle(background_color=COLOR_THEME['card']),
            footer=BlockStyle(background_color=COLOR_THEME['card'])
        )
    )

    return FlexSendMessage(alt_text="用藥管理選單", contents=bubble)
