import logging
import re

from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, BubbleStyle, BlockStyle, SeparatorComponent
)

from app.utils.menu import create_button
from app.utils.theme import COLOR_THEME

logger = logging.getLogger(__name__)

# ===== In-memory 資料暫存區 =====
medications_db = []  # 每筆: {'id', 'user_id', 'name', 'time'}
medication_id_counter = [1]
add_medication_state = {}  # 新增藥品狀態追蹤


def is_valid_time_format(time_str):
    """驗證時間格式 HH:MM"""
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    return bool(re.match(pattern, time_str))


def medication_exists(user_id, name, time):
    """檢查是否已存在相同藥品和時間"""
    meds = get_medications(user_id)
    return any(m['name'].lower() == name.lower() and m['time'] == time for m in meds)


def add_medication(user_id, name, time):
    """新增藥品"""
    # 檢查重複性
    if medication_exists(user_id, name, time):
        return None, "此藥品和時間已存在"

    med_id = medication_id_counter[0]
    medication_id_counter[0] += 1
    medications_db.append({
        'id': med_id,
        'user_id': user_id,
        'name': name,
        'time': time
    })
    logger.info(f"新增藥品: {name} @ {time} for {user_id}")
    return med_id, "新增成功！"


def get_medications(user_id):
    """取得用戶的所有藥品，按時間排序"""
    meds = [m for m in medications_db if m['user_id'] == user_id]
    return sorted(meds, key=lambda x: x['time'])


def delete_medication(user_id, med_id):
    """刪除藥品"""
    global medications_db
    original_count = len(medications_db)
    medications_db = [m for m in medications_db if not (m['user_id'] == user_id and m['id'] == med_id)]
    success = len(medications_db) < original_count
    logger.info(f"刪除藥品: {med_id} for {user_id}, 成功: {success}")
    return success


def start_add_medication(user_id):
    """開始新增藥品流程"""
    add_medication_state[user_id] = {"step": 1, "name": None}


def set_medication_name(user_id, name):
    """設定藥品名稱"""
    if user_id in add_medication_state:
        add_medication_state[user_id]["name"] = name.strip()
        add_medication_state[user_id]["step"] = 2


def finish_add_medication(user_id, time):
    """完成新增藥品"""
    if user_id in add_medication_state and add_medication_state[user_id]["step"] == 2:
        # 驗證時間格式
        time = time.strip()
        if not is_valid_time_format(time):
            return False, "時間格式錯誤，請使用 HH:MM 格式（例如：08:30）"

        name = add_medication_state[user_id]["name"]
        med_id, message = add_medication(user_id, name, time)

        if med_id is not None:
            del add_medication_state[user_id]
            return True, message
        else:
            return False, message
    return False, "新增失敗，請重新開始。"


def cancel_add_medication(user_id):
    """取消新增藥品流程"""
    if user_id in add_medication_state:
        del add_medication_state[user_id]
        return True
    return False


def is_adding_medication(user_id):
    """檢查是否正在新增藥品"""
    return user_id in add_medication_state


def get_add_medication_step(user_id):
    """取得新增藥品的步驟"""
    if user_id in add_medication_state:
        return add_medication_state[user_id]["step"]
    return 0


def get_medication_menu():
    """主選單"""
    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(
                    text="用藥管理",
                    weight="bold",
                    size="xl",
                    align="center",
                    color=COLOR_THEME['text_primary']
                ),
                TextComponent(
                    text="管理您的用藥提醒",
                    size="sm",
                    color=COLOR_THEME['text_secondary'],
                    align="center",
                    margin="sm"
                ),
                SeparatorComponent(margin="lg", color=COLOR_THEME['separator'])
            ],
            spacing="md",
            padding_all="lg",
            background_color=COLOR_THEME['card']
        ),
        footer=BoxComponent(
            layout="vertical",
            contents=[
                create_button("藥品清單", "med_list", COLOR_THEME['primary']),
                create_button("今日記錄", "med_today", COLOR_THEME['info'])
            ],
            spacing="sm",
            padding_all="lg",
            background_color=COLOR_THEME['card']
        ),
        styles=BubbleStyle(
            body=BlockStyle(background_color=COLOR_THEME['card']),
            footer=BlockStyle(background_color=COLOR_THEME['card'])
        )
    )
    return FlexSendMessage(alt_text="用藥管理", contents=bubble)


def get_medication_list_flex(user_id):
    """藥品清單介面"""
    meds = get_medications(user_id)

    # 新增按鈕
    add_button = create_button("➕ 新增藥品", "start_add_medication", COLOR_THEME['success'])

    if not meds:
        # 空清單
        bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="藥品清單",
                        weight="bold",
                        size="xl",
                        align="center",
                        color=COLOR_THEME['text_primary']
                    ),
                    SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                    TextComponent(
                        text="尚未新增任何藥品\n點擊下方按鈕開始新增",
                        size="md",
                        color=COLOR_THEME['text_secondary'],
                        align="center",
                        margin="lg",
                        wrap=True
                    )
                ],
                padding_all="lg",
                background_color=COLOR_THEME['card']
            ),
            footer=BoxComponent(
                layout="vertical",
                contents=[add_button],
                padding_all="lg",
                background_color=COLOR_THEME['card']
            ),
            styles=BubbleStyle(
                body=BlockStyle(background_color=COLOR_THEME['card']),
                footer=BlockStyle(background_color=COLOR_THEME['card'])
            )
        )
    else:
        # 有藥品的清單
        med_items = []
        for i, med in enumerate(meds):
            med_items.append(
                BoxComponent(
                    layout="horizontal",
                    contents=[
                        BoxComponent(
                            layout="vertical",
                            contents=[
                                TextComponent(
                                    text=med['name'],
                                    size="md",
                                    color=COLOR_THEME['text_primary'],
                                    weight="bold"
                                ),
                                TextComponent(
                                    text=f"{med['time']}",
                                    size="sm",
                                    color=COLOR_THEME['text_secondary']
                                )
                            ],
                            flex=4
                        ),
                        create_button("⨉", f"delete_medication_{med['id']}", COLOR_THEME['error'], flex=1)
                    ],
                    margin="md",
                    padding_all="sm"
                )
            )
            # 不是最後一個就加分隔線
            if i < len(meds) - 1:
                med_items.append(SeparatorComponent(margin="sm", color=COLOR_THEME['separator']))

        bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="藥品清單",
                        weight="bold",
                        size="xl",
                        align="center",
                        color=COLOR_THEME['text_primary']
                    ),
                    TextComponent(
                        text=f"共 {len(meds)} 項藥品",
                        size="sm",
                        color=COLOR_THEME['text_secondary'],
                        align="center",
                        margin="sm"
                    ),
                    SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                    *med_items
                ],
                padding_all="lg",
                background_color=COLOR_THEME['card']
            ),
            footer=BoxComponent(
                layout="vertical",
                contents=[add_button],
                padding_all="lg",
                background_color=COLOR_THEME['card']
            ),
            styles=BubbleStyle(
                body=BlockStyle(background_color=COLOR_THEME['card']),
                footer=BlockStyle(background_color=COLOR_THEME['card'])
            )
        )

    return FlexSendMessage(alt_text="藥品清單", contents=bubble)


def get_time_select_menu(user_id=None):
    """時間選擇選單"""
    # 只提供常用時間
    common_times = ["08:00", "12:00", "18:00", "21:00"]

    buttons = []
    for time in common_times:
        buttons.append(
            create_button(f"{time}", f"add_medication_time={time}", COLOR_THEME['primary'])
        )

    # 自訂時間選項
    buttons.append(
        create_button("其他時間", "custom_time", COLOR_THEME['info'])
    )

    # 取消按鈕
    buttons.append(
        create_button("取消", "cancel_add_medication", COLOR_THEME['error'])
    )

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(
                    text="選擇提醒時間",
                    weight="bold",
                    size="xl",
                    align="center",
                    color=COLOR_THEME['text_primary']
                ),
                TextComponent(
                    text="請選擇藥品提醒時間",
                    size="sm",
                    color=COLOR_THEME['text_secondary'],
                    align="center",
                    margin="sm"
                ),
                SeparatorComponent(margin="lg", color=COLOR_THEME['separator'])
            ],
            padding_all="lg",
            background_color=COLOR_THEME['card']
        ),
        footer=BoxComponent(
            layout="vertical",
            contents=buttons,
            spacing="sm",
            padding_all="lg",
            background_color=COLOR_THEME['card']
        ),
        styles=BubbleStyle(
            body=BlockStyle(background_color=COLOR_THEME['card']),
            footer=BlockStyle(background_color=COLOR_THEME['card'])
        )
    )

    return FlexSendMessage(alt_text="選擇提醒時間", contents=bubble)


def get_today_records(user_id):
    """今日記錄"""
    meds = get_medications(user_id)

    if not meds:
        bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="今日記錄",
                        weight="bold",
                        size="xl",
                        align="center",
                        color=COLOR_THEME['text_primary']
                    ),
                    SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                    TextComponent(
                        text="尚未設定任何藥品提醒",
                        size="md",
                        color=COLOR_THEME['text_secondary'],
                        align="center",
                        margin="lg"
                    )
                ],
                padding_all="lg",
                background_color=COLOR_THEME['card']
            ),
            styles=BubbleStyle(body=BlockStyle(background_color=COLOR_THEME['card']))
        )
    else:
        med_status = []
        for med in meds:
            med_status.append(
                BoxComponent(
                    layout="horizontal",
                    contents=[
                        TextComponent(
                            text=f"{med['name']}",
                            size="md",
                            color=COLOR_THEME['text_primary'],
                            flex=3
                        ),
                        TextComponent(
                            text=med['time'],
                            size="sm",
                            color=COLOR_THEME['text_secondary'],
                            flex=2
                        ),
                        TextComponent(
                            text="⏳ 待服用",
                            size="sm",
                            color=COLOR_THEME['warning'],
                            flex=2
                        )
                    ],
                    margin="md"
                )
            )

        bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="今日記錄",
                        weight="bold",
                        size="xl",
                        align="center",
                        color=COLOR_THEME['text_primary']
                    ),
                    TextComponent(
                        text=f"今日共有 {len(meds)} 項用藥",
                        size="sm",
                        color=COLOR_THEME['text_secondary'],
                        align="center",
                        margin="sm"
                    ),
                    SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                    *med_status
                ],
                padding_all="lg",
                background_color=COLOR_THEME['card']
            ),
            styles=BubbleStyle(body=BlockStyle(background_color=COLOR_THEME['card']))
        )

    return FlexSendMessage(alt_text="今日記錄", contents=bubble)
