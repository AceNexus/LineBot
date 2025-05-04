from linebot.models import (
    BubbleContainer, FlexSendMessage, BoxComponent,
    TextComponent, URIAction
)


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
        ("Java Message Service", "https://pse.is/7j2gxm"),
        ("ActiveMQ", "https://pse.is/7j2jaf"),
        ("Spring Cloud Eureka", "https://pse.is/7j2gyt"),
        ("Spring Cloud Config", "https://pse.is/7j2gzd"),
        ("Spring Cloud Gateway", "https://pse.is/7j2gzs"),
        ("Docker", "https://pse.is/7j2gvc"),
        ("Nginx", "https://pse.is/7j2gw5"),
        ("Database", "https://pse.is/7j2gwq"),
        ("LINE Bot", "https://pse.is/7j2h2j"),
        ("VirtualBox", "https://pse.is/7j2j9a")
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
                    color="#1DB446",
                    align="center",
                    wrap=True,
                    action=URIAction(label=name, uri=url)
                )
            ],
            padding_all="md",
            border_color="#1DB446",
            border_width="normal",
            corner_radius="md",
            margin="sm"
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
