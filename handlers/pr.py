import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import db
from config import config
from states import PRForm
from keyboards import main_menu, pr_moderation_kb

logger = logging.getLogger(__name__)
router = Router()


@router.message(PRForm.waiting_referrer)
async def process_referrer(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "cancel", "отменить"]:
        await state.clear()
        return await message.answer("❌ Заявка отменена.", reply_markup=main_menu())

    referrer_text = message.text.strip()
    await state.update_data(referrer_text=referrer_text)
    await state.clear()

    user_id = message.from_user.id
    username = message.from_user.username or "нет username"

    try:
        # Сохраняем заявку со статусом pending
        await db.upsert_role(
            user_id=user_id,
            role="pr",
            status="pending",
            referrer_text=referrer_text
        )

        await message.answer(
            "✅ <b>Ваша заявка на пиарщика отправлена!</b>\n\n"
            "Менеджер рассмотрит её в ближайшее время и свяжется с вами.\n"
            "Спасибо за интерес к команде A.T.L.A.S.!",
            parse_mode="HTML",
            reply_markup=main_menu()
        )

        # Уведомляем владельца с кнопками модерации
        notification = (
            f"🆕 <b>Новая заявка на пиарщика!</b>\n\n"
            f"👤 <b>Пользователь:</b> <code>{user_id}</code> (@{username})\n"
            f"📝 <b>Информация:</b> {referrer_text}"
        )

        try:
            await message.bot.send_message(
                config.owner_id,
                notification,
                parse_mode="HTML",
                reply_markup=pr_moderation_kb(user_id)
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления владельца: {e}")

        # Отправляем активным менеджерам
        managers = await db.list_managers()
        for m in managers:
            if m.get("status") == "active":
                try:
                    await message.bot.send_message(
                        m["telegram_id"],
                        notification,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Ошибка уведомления менеджера {m['telegram_id']}: {e}")

    except Exception as e:
        logger.error(f"Ошибка обработки заявки pr: {e}")
        await message.answer(
            "❌ Произошла ошибка при отправке заявки. Попробуйте позже.",
            reply_markup=main_menu()
        )
