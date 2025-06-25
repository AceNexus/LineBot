import logging

from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, ButtonComponent, PostbackAction,
    BubbleStyle, BlockStyle, SeparatorComponent
)

from app.utils.theme import COLOR_THEME

logger = logging.getLogger(__name__)


def create_button(label, action, color, emoji=None, flex=None):
    btn_label = f"{emoji} {label}" if emoji else label
    kwargs = {}
    if flex is not None:
        kwargs['flex'] = flex
    return ButtonComponent(
        action=PostbackAction(
            label=btn_label,
            data=f"action={action}"
        ),
        style="primary",
        color=color,
        margin="sm",
        height="sm",
        **kwargs
    )


def get_menu():
    title = TextComponent(
        text="AI 功能選單",
        weight="bold",
        size="xl",
        align="center",
        color=COLOR_THEME['text_primary'],
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇一項功能開始操作",
        size="sm",
        color=COLOR_THEME['text_secondary'],
        align="center",
        wrap=True,
        margin="sm"
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[
            title,
            subtitle,
            SeparatorComponent(margin="lg", color=COLOR_THEME['separator'])
        ],
        spacing="md",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    buttons = [
        create_button("新聞快訊", "news", COLOR_THEME['primary'], emoji="📰"),
        create_button("熱門電影", "movie", COLOR_THEME['info'], emoji="🎬"),
        create_button("日文單字", "japanese", COLOR_THEME['primary'], emoji="🇯🇵"),
        create_button("英文單字", "english", COLOR_THEME['info'], emoji="🇺🇸"),
        create_button("英文訂閱", "english_subscribe", COLOR_THEME['primary'], emoji="📅"),
        create_button("用藥管理", "medication_menu", COLOR_THEME['info'], emoji="💊"),
        create_button("AI 回應開關", "toggle_ai", COLOR_THEME['primary'], emoji="🤖")
    ]

    footer_box = BoxComponent(
        layout="vertical",
        contents=buttons,
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

    return FlexSendMessage(alt_text="功能選單", contents=bubble)
