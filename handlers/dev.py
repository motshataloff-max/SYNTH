import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import db
from config import config
from states import DevForm
from keyboards import main_menu, dev_moderation_kb

logger = logging.getLogger(__name__)
router = Router()


@router.message(DevForm.name)
async def process_name(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "cancel", "отменить"]:
        await state.clear()
        return await message.answer("❌ Заявка отменена.", reply_markup=main_menu())

    await state.update_data(name=message.text.strip())
    await state.set_state(DevForm.experience)
    await message.answer(
        "📝 <b>Шаг 2/4:</b> Опишите свой опыт в разработке.\n"
        "<i>Какие языки знаете, какие проекты делали?</i>",
        parse_mode="HTML"
    )


@router.message(DevForm.experience)
async def process_experience(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "cancel", "отменить"]:
        await state.clear()
        return await message.answer("❌ Заявка отменена.", reply_markup=main_menu())

    await state.update_data(experience=message.text.strip())
    await state.set_state(DevForm.level)
    await message.answer(
        "📝 <b>Шаг 3/4:</b> На какой уровень претендуете?\n\n"
        "• <b>junior</b> — начинающий\n"
        "• <b>medium</b> — средний уровень\n"
        "• <b>senior</b> — опытный разработчик\n\n"
        "Напишите одно слово: <code>junior</code>, <code>medium</code> или <code>senior</code>",
        parse_mode="HTML"
    )


@router.message(DevForm.level)
async def process_level(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "cancel", "отменить"]:
        await state.clear()
        return await message.answer("❌ Заявка отменена.", reply_markup=main_menu())

    level = message.text.strip().lower()
    if level not in ["junior", "medium", "senior"]:
        return await message.answer(
            "⚠️ Пожалуйста, напишите одно из трёх: <code>junior</code>, <code>medium</code> или <code>senior</code>",
            parse_mode="HTML"
        )

    await state.update_data(level=level)
    await state.set_state(DevForm.portfolio)
    await message.answer(
        "📝 <b>Шаг 4/4:</b> Ссылка на портфолио (GitHub, сайт, примеры работ).\n"
        "<i>Если нет портфолио — напишите 'нет'</i>",
        parse_mode="HTML"
    )


@router.message(DevForm.portfolio)
async def process_portfolio(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "cancel", "отменить"]:
        await state.clear()
        return await message.answer("❌ Заявка отменена.", reply_markup=main_menu())

    portfolio = message.text.strip()
    data = await state.get_data()
    await state.clear()

    user_id = message.from_user.id
    username = message.from_user.username or "нет username"

    try:
        # Сохраняем заявку со статусом pending
        await db.upsert_role(
            user_id=user_id,
            role="dev",
            status="pending",
            level=data["level"],
            referrer_text=(
                f"Имя: {data['name']}\n"
                f"Опыт: {data['experience']}\n"
                f"Портфолио: {portfolio}"
            )
        )

        await message.answer(
            "✅ <b>Ваша заявка на разработчика отправлена!</b>\n\n"
            "Менеджер рассмотрит её в ближайшее время и свяжется с вами.\n"
            "Спасибо за интерес к команде A.T.L.A.S.!",
            parse_mode="HTML",
            reply_markup=main_menu()
        )

        # Уведомляем владельца и менеджеров
        notification = (
            f"🆕 <b>Новая заявка на разработчика!</b>\n\n"
            f"👤 <b>Пользователь:</b> <code>{user_id}</code> (@{username})\n"
            f"📝 <b>Имя:</b> {data['name']}\n"
            f"🎯 <b>Уровень:</b> {data['level']}\n"
            f"💼 <b>Опыт:</b> {data['experience']}\n"
            f"🔗 <b>Портфолио:</b> {portfolio}"
        )

        # Отправляем владельцу с кнопками модерации
        try:
            await message.bot.send_message(
                config.owner_id,
                notification,
                parse_mode="HTML",
                reply_markup=dev_moderation_kb(user_id)
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
        logger.error(f"Ошибка обработки заявки dev: {e}")
        await message.answer(
            "❌ Произошла ошибка при отправке заявки. Попробуйте позже.",
            reply_markup=main_menu()
        )
