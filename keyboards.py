from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


# ==========================================
# ГЛАВНЫЕ МЕНЮ (Reply-клавиатуры)
# ==========================================

def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню для всех пользователей."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🛒 Заказать разработку"),
                KeyboardButton(text="👨‍💻 Стать разработчиком"),
            ],
            [
                KeyboardButton(text="🧪 Стать тестировщиком"),
                KeyboardButton(text="📣 Стать пиарщиком"),
            ],
            [
                KeyboardButton(text="📊 Моя статистика"),
                KeyboardButton(text="ℹ️ О нас"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие 👇",
    )


def admin_menu() -> ReplyKeyboardMarkup:
    """Админское меню (видно только CEO и менеджерам)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Список проектов"),
                KeyboardButton(text="👥 Менеджеры"),
            ],
            [
                KeyboardButton(text="👨‍💻 Разработчики"),
                KeyboardButton(text="🧪 Тестировщики"),
            ],
            [
                KeyboardButton(text="📈 Статистика бота"),
                KeyboardButton(text="⚙️ Настройки"),
            ],
            [
                KeyboardButton(text="🔙 Главное меню"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Админ-панель 👑",
    )


# ==========================================
# ДЕЙСТВИЯ С ПРОЕКТАМИ (Inline-клавиатуры)
# ==========================================

def project_actions_kb(project_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с действиями для конкретного проекта."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚙️ Назначить",
                    callback_data=f"proj_assign_{project_id}"
                ),
                InlineKeyboardButton(
                    text="✅ Завершить",
                    callback_data=f"proj_complete_{project_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💸 Неоплачено",
                    callback_data=f"proj_unpaid_{project_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"proj_cancel_{project_id}"
                ),
            ],
        ]
    )


# ==========================================
# МОДЕРАЦИЯ РАЗРАБОТЧИКОВ
# ==========================================

def dev_moderation_kb(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для одобрения/отклонения заявки разработчика."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"dev_approve_{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"dev_reject_{user_id}"
                ),
            ]
        ]
    )


# ==========================================
# МОДЕРАЦИЯ ТЕСТЕРОВ
# ==========================================

def tester_moderation_kb(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для одобрения/отклонения заявки тестировщика."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"tester_approve_{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"tester_reject_{user_id}"
                ),
            ]
        ]
    )


# ==========================================
# МОДЕРАЦИЯ ПИАРЩИКОВ
# ==========================================

def pr_moderation_kb(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для одобрения/отклонения заявки пиарщика."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"pr_approve_{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"pr_reject_{user_id}"
                ),
            ]
        ]
    )


# ==========================================
# УПРАВЛЕНИЕ МЕНЕДЖЕРАМИ
# ==========================================

def manager_actions_kb(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления менеджером."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏸ Отстранить",
                    callback_data=f"manager_suspend_{user_id}"
                ),
                InlineKeyboardButton(
                    text="▶️ Вернуть",
                    callback_data=f"manager_resume_{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"manager_remove_{user_id}"
                ),
            ],
        ]
    )


# ==========================================
# ВЫБОР УРОВНЯ (для разработчиков и тестеров)
# ==========================================

def dev_level_kb(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора уровня разработчика."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔴 Senior", callback_data=f"dev_level_{user_id}_senior"),
                InlineKeyboardButton(text="🟡 Medium", callback_data=f"dev_level_{user_id}_medium"),
            ],
            [
                InlineKeyboardButton(text="🟢 Junior", callback_data=f"dev_level_{user_id}_junior"),
            ],
        ]
    )


def tester_level_kb(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора уровня тестировщика."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 Начинающий", callback_data=f"tester_level_{user_id}_beginner"),
                InlineKeyboardButton(text="🔵 Опытный", callback_data=f"tester_level_{user_id}_experienced"),
            ],
        ]
    )


# ==========================================
# НАВИГАЦИЯ И ОТМЕНА
# ==========================================

def cancel_kb() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


def back_to_menu_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")],
        ]
    )


def yes_no_kb(action: str) -> InlineKeyboardMarkup:
    """Универсальная клавиатура Да/Нет для подтверждения действий."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"{action}_yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"{action}_no"),
            ],
        ]
    )
