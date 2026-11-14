from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
import logging

import db
from config import config
from states import ClientForm
from keyboards import main_menu

logger = logging.getLogger(__name__)
router = Router()


@router.message(ClientForm.title)
async def process_title(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "cancel", "отменить"]:
        await state.clear()
        return await message.answer("❌ Заказ отменен.", reply_markup=main_menu())
    
    await state.update_data(title=message.text.strip())
    await state.set_state(ClientForm.description)
    await message.answer(
        "📝 Отлично! Теперь кратко опишите, что нужно сделать (ТЗ):\n"
        "<i>(Например: 'Парсер авито на питоне с сохранением в Excel')</i>",
        parse_mode="HTML"
    )


@router.message(ClientForm.description)
async def process_description(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "cancel", "отменить"]:
        await state.clear()
        return await message.answer("❌ Заказ отменен.", reply_markup=main_menu())

    await state.update_data(description=message.text.strip())
    await state.set_state(ClientForm.budget)
    await message.answer(
        "💰 Какой бюджет вы готовы предложить в Telegram Stars?\n"
        "<i>(Введите только число, например: 500)</i>",
        parse_mode="HTML"
    )


@router.message(ClientForm.budget)
async def process_budget(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "cancel", "отменить"]:
        await state.clear()
        return await message.answer("❌ Заказ отменен.", reply_markup=main_menu())

    if not message.text.isdigit():
        return await message.answer("⚠️ Бюджет должен быть числом. Попробуйте еще раз или напишите /cancel")

    budget = int(message.text)
    if budget < 50: 
        return await message.answer("⚠️ Минимальный бюджет для заказа — 50 ⭐. Попробуйте еще раз или напишите /cancel")

    await state.update_data(budget=budget)
    data = await state.get_data()
    await state.clear()

    client_id = message.from_user.id
    
    # Получаем referrer_id, если он был сохранен при регистрации
    user = await db.get_user(client_id)
    referrer_id = user["referrer_id"] if user else None

    # Назначаем менеджера (по кругу)
    manager_id = await db.next_recipient(config.owner_id)

    try:
        project_id = await db.create_project(
            client_id=client_id,
            title=data["title"],
            description=data["description"],
            budget=budget,
            referrer_id=referrer_id,
            manager_id=manager_id
        )
        
        success_text = (
            f"✅ <b>Ваша заявка успешно создана!</b>\n\n"
            f"📌 <b>ID проекта:</b> <code>{project_id}</code>\n"
            f"📝 <b>Название:</b> {data['title']}\n"
            f"💰 <b>Бюджет:</b> {budget} ⭐\n\n"
            f"👨‍💼 Менеджер скоро свяжется с вами для уточнения деталей."
        )
        await message.answer(success_text, parse_mode="HTML", reply_markup=main_menu())

        # Уведомляем менеджера и владельца
        manager_text = (
            f"🆕 <b>Новый заказ!</b>\n\n"
            f"📌 <b>ID:</b> <code>{project_id}</code>\n"
            f"👤 <b>Клиент:</b> <code>{client_id}</code> (@{message.from_user.username or 'нет username'})\n"
            f"📝 <b>ТЗ:</b> {data['title']}\n{data['description']}\n"
            f"💰 <b>Бюджет:</b> {budget} ⭐"
        )
        
        try:
            await message.bot.send_message(manager_id, manager_text, parse_mode="HTML")
            if manager_id != config.owner_id:
                await message.bot.send_message(config.owner_id, manager_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка уведомления менеджера: {e}")

    except Exception as e:
        logger.error(f"Ошибка создания проекта: {e}")
        await message.answer("❌ Произошла ошибка при создании заказа. Попробуйте позже или напишите администратору.", reply_markup=main_menu())
