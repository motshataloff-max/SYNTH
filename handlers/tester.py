import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import db
from config import config
from states import TesterForm
from keyboards import main_menu, tester_moderation_kb

logger = logging.getLogger(__name__)
router = Router()


@router.message(TesterForm.name)
async def process_name(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "cancel", "отменить"]:
        await state.clear()
        return await message.answer("❌ Заявка отменена.", reply_markup=main_menu())

    await state.update_data(name=message.text.strip())
    await state.set_state(TesterForm.experience)
    await message.answer(
        "📝 <b>Шаг 2/3:</b> Опишите свой опыт в тестировании.\n"
        "<i>Какие инструменты знаете, какие проекты тестировали?</i>",
        parse_mode="HTML"
    )


@router.message(TesterForm.experience)
async def process_experience(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "cancel", "отменить"]:
        await state.clear()
        return await message.answer("❌ Заявка отменена.", reply_markup=main_menu())

    await state.update_data(experience=message.text.strip())
    await state.set_state(TesterForm.level)
    await message.answer(
        "📝 <b>Шаг 3/3:</b> На какой уровень претендуете?\n\n"
        "• <b>beginner</b> — начинающий тестировщик\n"
        "• <b>experienced</b> — опытный тестировщик\n\n"
        "Напишите одно слово: <code>beginner</code> или <code>experienced</code>",
        parse_mode="HTML"
    )


@router.message(TesterForm.level)
async def process_level(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "cancel", "отменить"]:
        await state.clear()
        return await message.answer("❌ Заявка отменена.", reply_markup=main_menu())

    level = message.text.strip().lower()
    if level not in ["beginner", "experienced"]:
        return await message.answer(
            "⚠️ Пожалуйста, напишите одно из двух: <code>beginner</code> или <code>experienced</code>",
            parse_mode="HTML"
        )

    data = await state.get_data()
    await state.clear()

    user_id = message.from_user.id
    username = message.from_user.username or "нет username"

    try:
        # Сохраняем заявку со статусом pending
        await db.upsert_role(
            user_id=user_id,
            role="tester",
            status="pending",
            level=level,
            referrer_text=(
                f"Имя: {data['name']}\n"
                f"Опыт: {data['experience']}"
            )
        )

        await message.answer(
            "✅ <b>Ваша заявка на тестировщика отправлена!</b>\n\n"
            "Менеджер рассмотрит её в ближайшее время и свяжется с вами.\n"
            "Спасибо за интерес к команде A.T.L.A.S.!",
            parse_mode="HTML",
            reply_markup=main_menu()
        )

        # Уведомляем владельца с кнопками модерации
        notification = (
            f"🆕 <b>Новая заявка на тестировщика!</b>\n\n"
            f"👤 <b>Пользователь:</b> <code>{user_id}</code> (@{username})\n"
            f"📝 <b>Имя:</b> {data['name']}\n"
            f"🎯 <b>Уровень:</b> {level}\n"
            f"💼 <b>Опыт:</b> {data['experience']}"
        )

        try:
            await message.bot.send_message(
                config.owner_id,
                notification,
                parse_mode="HTML",
                reply_markup=tester_moderation_kb(user_id)
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
        logger.error(f"Ошибка обработки заявки tester: {e}")
        await message.answer(
            "❌ Произошла ошибка при отправке заявки. Попробуйте позже.",
            reply_markup=main_menu()
        )
