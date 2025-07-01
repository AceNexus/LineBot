from linebot.models import (
    BubbleContainer, FlexSendMessage, BoxComponent,
    TextComponent, URIAction, BubbleStyle, BlockStyle
)

from app.utils.theme import COLOR_THEME


def get_lumos():
    title = TextComponent(
        text="技術資源分享",
        weight="bold",
        size="xl",
        align="center",
        color=COLOR_THEME['text_primary'],
        wrap=True
    )

    subtitle = TextComponent(
        text="點選下方按鈕開啟",
        size="sm",
        color=COLOR_THEME['text_secondary'],
        align="center",
        wrap=True
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[title, subtitle],
        spacing="md",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    resources = [
        ("Git", "https://pse.is/7j2gcd"),
        ("IntelliJ", "https://pse.is/7j2gem"),
        ("Java", "https://pse.is/7j2gk2"),
        ("Spring Boot (1)", "https://pse.is/7j2jtm"),
        ("Spring Boot (2)", "https://pse.is/7j2gu8"),
        ("Java Message Service", "https://pse.is/7j2gxm"),
        ("ActiveMQ", "https://pse.is/7j2jaf"),
        ("Spring Cloud Eureka", "https://pse.is/7j2gyt"),
        ("Spring Cloud Config", "https://pse.is/7j2gzd"),
        ("Spring Cloud Gateway", "https://pse.is/7j2gzs"),
        ("Docker", "https://pse.is/7j2gvc"),
        ("Nginx", "https://pse.is/7j2gw5"),
        ("Database", "https://pse.is/7j2gwq"),
        ("LINE Bot", "https://pse.is/7j2h2j"),
        ("VirtualBox", "https://pse.is/7j2j9a"),
        ("Ngrok", "https://pse.is/7tkylz")
    ]

    footer_contents = []

    for name, url in resources:
        footer_contents.append(BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(
                    text=name,
                    size="md",
                    weight="bold",
                    color=COLOR_THEME['info'],
                    align="center",
                    wrap=True,
                    action=URIAction(label=name, uri=url)
                )
            ],
            padding_all="md",
            border_color=COLOR_THEME['separator'],
            border_width="normal",
            corner_radius="md",
            margin="sm",
            background_color=COLOR_THEME['card']
        ))

    footer_box = BoxComponent(
        layout="vertical",
        contents=footer_contents,
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

    return FlexSendMessage(alt_text="技術學習資源", contents=bubble)
