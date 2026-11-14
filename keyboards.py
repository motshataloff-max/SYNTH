from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Заказать разработку")],
            [KeyboardButton(text="👨‍💻 Стать разработчиком"),
             KeyboardButton(text="🧪 Стать тестировщиком")],
            [KeyboardButton(text="📣 Стать пиарщиком")],
            [KeyboardButton(text="📊 Моя статистика")],
            [KeyboardButton(text="ℹ️ О нас")],
        ],
        resize_keyboard=True,
    )


def pr_moderation_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"pr:approve:{user_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"pr:reject:{user_id}"),
    ]])


def dev_moderation_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"dev:approve:{user_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"dev:reject:{user_id}"),
    ]])


def tester_moderation_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"tester:approve:{user_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"tester:reject:{user_id}"),
    ]])

def project_actions_kb(project_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Завершить", callback_data=f"proj:complete:{project_id}"),
            InlineKeyboardButton(text="👥 Назначить", callback_data=f"proj:assign:{project_id}"),
        ],
        [
            InlineKeyboardButton(text="💰 Не оплачено", callback_data=f"proj:unpaid:{project_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"proj:cancel:{project_id}"),
        ],
    ])