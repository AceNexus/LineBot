import logging

logger = logging.getLogger(__name__)


def get_menu():
    return (
        "請輸入數字選擇查詢項目：\n"
        "1. 新聞\n"
        "2. 電影\n"
        "3. 日文單字\n"
        "4. 英文單字\n"
        "\n提示：輸入「lumos」or「路摸思」可以查看隱藏功能"
    )
