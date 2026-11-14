from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
from keyboards import main_menu, project_actions_kb
from states import ClientForm
from config import config

router = Router()


@router.message(ClientForm.title)
async def order_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()
    if not title:
        await message.answer("Напишите имя или название проекта.")
        return
    await state.update_data(title=title[:200])
    await state.set_state(ClientForm.description)
    await message.answer("Кратко опишите задачу.")


@router.message(ClientForm.description)
async def order_description(message: Message, state: FSMContext):
    desc = (message.text or "").strip()
    if len(desc) < 5:
        await message.answer("Опишите чуть подробнее (минимум 5 символов).")
        return
    await state.update_data(description=desc[:2000])
    await state.set_state(ClientForm.budget)
    await message.answer("Предполагаемый бюджет в Stars (целое число).")


@router.message(ClientForm.budget)
async def order_budget(message: Message, state: FSMContext, bot: Bot):
    raw = (message.text or "").strip()
    if not raw.isdigit() or int(raw) <= 0:
        await message.answer("Введите целое положительное число Stars.")
        return
    budget = int(raw)

    data = await state.get_data()
    await state.clear()

    client = await db.get_or_create_user(message.from_user)
    referrer_id = client["referrer_id"] if client else None

    recipient_id = await db.next_recipient(config.owner_id)
    project_id = await db.create_project(
        client_id=message.from_user.id,
        title=data["title"],
        description=data["description"],
        budget=budget,
        referrer_id=referrer_id,
        manager_id=recipient_id,
    )

    await message.answer(
        f"✅ Заявка принята. Номер: <b>#{project_id}</b>\n"
        f"Менеджер свяжется с вами.",
        reply_markup=main_menu(),
    )

    notify = (
        f"🆕 <b>Новая заявка #{project_id}</b>\n\n"
        f"Клиент: {message.from_user.full_name} "
        f"(@{message.from_user.username or '—'}, ID <code>{message.from_user.id}</code>)\n"
        f"Проект: <b>{data['title']}</b>\n"
        f"Описание: {data['description']}\n"
        f"Бюджет: <b>{budget} ⭐</b>\n"
        f"Реферер: {referrer_id or '—'}"
    )
    try:
        await bot.send_message(recipient_id, notify,
                               reply_markup=project_actions_kb(project_id))
    except Exception:
        await bot.send_message(config.owner_id,
                               notify + "\n\n⚠️ Не доставлено получателю.",
                               reply_markup=project_actions_kb(project_id))


@router.callback_query(F.data.startswith("proj:"))
async def project_actions(cb: CallbackQuery):
    uid = cb.from_user.id
    is_owner = uid == config.owner_id
    is_manager = await db.has_active_role(uid, "manager")
    if not (is_owner or is_manager):
        await cb.answer("Нет прав.", show_alert=True)
        return

    _, action, raw_id = cb.data.split(":")
    project_id = int(raw_id)

    if action == "cancel":
        await db.set_project_status(project_id, "canceled")
        await cb.message.edit_text(cb.message.html_text + "\n\n❌ Отменён")
        await cb.answer("Проект отменён.")
    elif action == "unpaid":
        await db.set_project_status(project_id, "unpaid")
        await cb.message.edit_text(cb.message.html_text + "\n\n💰 Не оплачено")
        await cb.answer("Статус: не оплачено.")
    else:
        await cb.answer("Используйте /complete или /assign.")