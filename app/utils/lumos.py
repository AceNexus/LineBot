import logging

from linebot.models import (
    FlexSendMessage,
    BubbleContainer,
    BoxComponent,
    TextComponent,
    ButtonComponent,
    URIAction,
    SeparatorComponent
)

logger = logging.getLogger(__name__)


def get_lumos():
    title = TextComponent(
        text="✨ 技術資源分享 ✨",
        weight="bold",
        size="xl",
        align="center",
        color="#1DB446",
        wrap=True
    )

    subtitle = TextComponent(
        text="點選下方按鈕開啟",
        size="sm",
        color="#888888",
        align="center",
        wrap=True
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[title, subtitle],
        spacing="md",
        padding_all="lg"
    )

    resources = [
        ("Git", "https://pse.is/7j2gcd"),
        ("IntelliJ", "https://pse.is/7j2gem"),
        ("Java", "https://pse.is/7j2gk2"),
        ("Spring Boot (1)", "https://pse.is/7j2jtm"),
        ("Spring Boot (2)", "https://pse.is/7j2gu8"),
        ("JMS", "https://pse.is/7j2gxm"),
        ("ActiveMQ", "https://pse.is/7j2jaf"),
        ("Eureka", "https://pse.is/7j2gyt"),
        ("Config", "https://pse.is/7j2gzd"),
        ("Gateway", "https://pse.is/7j2gzs"),
        ("Docker", "https://pse.is/7j2gvc"),
        ("Nginx", "https://pse.is/7j2gw5"),
        ("Database", "https://pse.is/7j2gwq"),
        ("LINE Bot", "https://pse.is/7j2h2j"),
        ("VirtualBox", "https://pse.is/7j2j9a")
    ]

    footer_contents = []
    for i, (name, url) in enumerate(resources):
        footer_contents.append(ButtonComponent(
            style="link",
            height="sm",
            action=URIAction(label=name, uri=url)
        ))
        # 加分隔線（除了最後一項）
        if i < len(resources) - 1:
            footer_contents.append(SeparatorComponent(
                margin="md"
            ))

    footer_box = BoxComponent(
        layout="vertical",
        contents=footer_contents,
        spacing="sm",
        padding_all="lg"
    )

    bubble = BubbleContainer(
        body=body_box,
        footer=footer_box
    )

    return FlexSendMessage(alt_text="技術學習資源", contents=bubble)
