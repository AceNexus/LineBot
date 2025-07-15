import logging
import re
from datetime import datetime

from linebot.models import ButtonComponent, PostbackAction, BoxComponent, TextComponent
from linebot.models import (
    FlexSendMessage, BubbleContainer, BubbleStyle, BlockStyle, SeparatorComponent
)

from app.utils.menu import create_button
from app.utils.theme import COLOR_THEME

logger = logging.getLogger(__name__)

# ===== 其他提醒固定時段，供全專案共用 =====
other_reminder_common_times = ["08:00", "12:00", "18:00", "21:00"]

# ===== In-memory 資料暫存區 =====
other_reminders_db = []  # 每筆: {'id', 'user_id', 'content', 'time'}
other_reminder_id_counter = [1]
add_other_reminder_state = {}  # 新增提醒狀態追蹤

# ===== 今日提醒狀態暫存區 =====
today_other_reminder_status = {}  # key: (user_id, content, time, date), value: True/False


def get_other_reminders_by_time(time_str):
    """取得指定時間的所有提醒清單，回傳 [(user_id, content)]"""
    return [(r['user_id'], r['content']) for r in other_reminders_db if r['time'] == time_str]


def is_valid_time_format(time_str):
    """驗證時間格式 HH:MM"""
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    return bool(re.match(pattern, time_str))


def other_reminder_exists(user_id, content, time):
    rems = get_other_reminders(user_id)
    return any(r['content'].lower() == content.lower() and r['time'] == time for r in rems)


def add_other_reminder(user_id, content, time):
    if other_reminder_exists(user_id, content, time):
        return None, "此提醒內容和時間已存在"
    rem_id = other_reminder_id_counter[0]
    other_reminder_id_counter[0] += 1
    other_reminders_db.append({
        'id': rem_id,
        'user_id': user_id,
        'content': content,
        'time': time
    })
    logger.info(f"新增提醒: {content} @ {time} for {user_id}")
    return rem_id, "新增成功！"


def get_other_reminders(user_id):
    rems = [r for r in other_reminders_db if r['user_id'] == user_id]
    return sorted(rems, key=lambda x: x['time'])


def start_add_other_reminder(user_id):
    add_other_reminder_state[user_id] = {"step": 1, "content": None}


def set_other_reminder_content(user_id, content):
    if user_id in add_other_reminder_state:
        add_other_reminder_state[user_id]["content"] = content.strip()
        add_other_reminder_state[user_id]["step"] = 2


def finish_add_other_reminder(user_id, time):
    if user_id in add_other_reminder_state and add_other_reminder_state[user_id]["step"] == 2:
        time = time.strip()
        if not is_valid_time_format(time):
            return False, "時間格式錯誤，請使用 HH:MM 格式（例如：08:30）"
        content = add_other_reminder_state[user_id]["content"]
        rem_id, message = add_other_reminder(user_id, content, time)
        if rem_id is not None:
            del add_other_reminder_state[user_id]
            return True, message
        else:
            return False, message
    return False, "新增失敗，請重新開始。"


def is_adding_other_reminder(user_id):
    return user_id in add_other_reminder_state


def cancel_add_other_reminder(user_id):
    add_other_reminder_state.pop(user_id, None)


def get_add_other_reminder_step(user_id):
    return add_other_reminder_state.get(user_id, {}).get("step", 0)


def mark_other_reminder_done(user_id, content, time, date):
    today_other_reminder_status[(user_id, content, time, date)] = True


def is_other_reminder_done(user_id, content, time, date):
    return today_other_reminder_status.get((user_id, content, time, date), False)


def delete_other_reminder(user_id, rem_id):
    global other_reminders_db
    before = len(other_reminders_db)
    other_reminders_db = [r for r in other_reminders_db if not (r['user_id'] == user_id and r['id'] == rem_id)]
    return len(other_reminders_db) < before


def get_other_reminder_menu():
    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(
                    text="其他提醒管理",
                    weight="bold",
                    size="xl",
                    align="center",
                    color=COLOR_THEME['text_primary']
                ),
                TextComponent(
                    text="管理您的其他提醒",
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
                create_button("提醒清單", "other_reminder_list", COLOR_THEME['primary'],
                              display_text="其他提醒：查看提醒清單"),
                create_button("今日記錄", "other_reminder_today", COLOR_THEME['info'],
                              display_text="其他提醒：查看今日記錄")
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
    return FlexSendMessage(alt_text="其他提醒管理", contents=bubble)


def get_other_reminder_list_flex(user_id):
    rems = get_other_reminders(user_id)
    add_button = create_button("➕ 新增提醒", "start_add_other_reminder", COLOR_THEME['success'],
                               display_text="其他提醒：新增提醒")
    if not rems:
        bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(
                        text="提醒清單",
                        weight="bold",
                        size="xl",
                        align="center",
                        color=COLOR_THEME['text_primary']
                    ),
                    SeparatorComponent(margin="lg", color=COLOR_THEME['separator']),
                    TextComponent(
                        text="尚未新增任何提醒\n點擊下方按鈕開始新增",
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
        rem_items = []
        for i, rem in enumerate(rems):
            rem_items.append(
                BoxComponent(
                    layout="horizontal",
                    contents=[
                        BoxComponent(
                            layout="vertical",
                            contents=[
                                TextComponent(
                                    text=rem['content'],
                                    size="md",
                                    color=COLOR_THEME['text_primary'],
                                    weight="bold"
                                ),
                                TextComponent(
                                    text=f"{rem['time']}",
                                    size="sm",
                                    color=COLOR_THEME['text_secondary']
                                )
                            ],
                            flex=4
                        ),
                        create_button("⨉", f"delete_other_reminder_{rem['id']}", COLOR_THEME['error'], flex=1,
                                      display_text=f"其他提醒：刪除提醒 {rem['content']}")
                    ],
                    margin="md",
                    padding_all="sm"
                )
            )
            if i < len(rems) - 1:
                rem_items.append(SeparatorComponent(margin="sm", color=COLOR_THEME['separator']))
        bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                             TextComponent(
                                 text="提醒清單",
                                 weight="bold",
                                 size="xl",
                                 align="center",
                                 color=COLOR_THEME['text_primary']
                             ),
                             SeparatorComponent(margin="lg", color=COLOR_THEME['separator'])
                         ] + rem_items,
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
    return FlexSendMessage(alt_text="提醒清單", contents=bubble)


def get_today_other_reminder_records(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    rems = get_other_reminders(user_id)
    if not rems:
        return TextComponent(text="今日尚無提醒記錄。", color=COLOR_THEME['text_secondary'])
    rem_status = []
    for rem in rems:
        done = is_other_reminder_done(user_id, rem['content'], rem['time'], today)
        status_text = "✅ 已完成" if done else "⏳ 待完成"
        status_color = COLOR_THEME['success'] if done else COLOR_THEME['warning']
        info_row = BoxComponent(
            layout="horizontal",
            contents=[
                TextComponent(text=f"{rem['content']}", size="md", color=COLOR_THEME['text_primary'], flex=3),
                TextComponent(text=rem['time'], size="sm", color=COLOR_THEME['text_secondary'], flex=2),
                TextComponent(text=status_text, size="sm", color=status_color, flex=2)
            ],
            margin="md"
        )
        rem_status.append(info_row)
        if not done:
            button_row = BoxComponent(
                layout="vertical",
                contents=[
                    ButtonComponent(
                        action=PostbackAction(
                            label="我已完成",
                            data=f"action=other_reminder_confirm&user_id={user_id}&content={rem['content']}&time={rem['time']}"
                        ),
                        style="primary",
                        color=COLOR_THEME['primary'],
                        height="sm"
                    )
                ],
                margin="sm"
            )
            rem_status.append(button_row)
    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=[
                         TextComponent(
                             text="今日提醒記錄",
                             weight="bold",
                             size="xl",
                             align="center",
                             color=COLOR_THEME['text_primary']
                         ),
                         SeparatorComponent(margin="lg", color=COLOR_THEME['separator'])
                     ] + rem_status,
            padding_all="lg",
            background_color=COLOR_THEME['card']
        ),
        styles=BubbleStyle(
            body=BlockStyle(background_color=COLOR_THEME['card'])
        )
    )
    return FlexSendMessage(alt_text="今日提醒記錄", contents=bubble)


def get_time_select_menu_other_reminder(user_id=None):
    buttons = []
    for time in other_reminder_common_times:
        buttons.append(
            create_button(f"{time}", f"add_other_reminder_time={time}", COLOR_THEME['primary'],
                          display_text=f"其他提醒：設定提醒時間 {time}"))
    buttons.append(
        create_button("其他時間", "custom_time_other_reminder", COLOR_THEME['info'],
                      display_text="其他提醒：自訂提醒時間")
    )
    buttons.append(
        create_button("取消", "cancel_add_other_reminder", COLOR_THEME['error'], display_text="其他提醒：取消新增提醒")
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
                    text="請選擇提醒時間",
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
