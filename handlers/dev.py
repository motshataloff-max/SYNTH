from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import db
import texts
from keyboards import dev_moderation_kb
from states import DevForm
from config import config

router = Router()

LEVELS = {"junior": "junior", "medium": "medium", "senior": "senior"}


@router.message(DevForm.name)
async def dev_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("Напишите имя.")
        return
    await state.update_data(name=name[:100])
    await state.set_state(DevForm.level)
    await message.answer(texts.DEV_ASK_LEVEL)


@router.message(DevForm.level)
async def dev_level(message: Message, state: FSMContext):
    raw = (message.text or "").strip().lower()
    if raw not in LEVELS:
        await message.answer("Напишите одно слово: Senior, Medium или Junior.")
        return
    await state.update_data(level=LEVELS[raw])
    await state.set_state(DevForm.solution)
    await message.answer(texts.DEV_TASKS[raw])


@router.message(DevForm.solution)
async def dev_solution(message: Message, state: FSMContext, bot: Bot):
    if not (message.text or message.document):
        await message.answer("Пришлите решение текстом или файлом.")
        return

    data = await state.get_data()
    await state.clear()
    uid = message.from_user.id
    level = data["level"]
    name = data["name"]

    await db.upsert_role(uid, "dev", status="pending", level=level)

    owner_text = (
        f"👨‍💻 <b>Заявка разработчика</b>\n\n"
        f"ID: <code>{uid}</code>\n"
        f"Имя: {name}\n"
        f"Username: @{message.from_user.username or '—'}\n"
        f"Уровень: <b>{level}</b>\n\n"
        f"<b>Решение:</b>"
    )
    await bot.send_message(config.owner_id, owner_text,
                           reply_markup=dev_moderation_kb(uid))

    if message.document:
        await bot.send_message(
            config.owner_id,
            f"📎 Файл от <code>{uid}</code>:",
            document=message.document.file_id,
        )
    else:
        text = message.text[:3500]
        await bot.send_message(config.owner_id, f"<pre>{text}</pre>")

    await message.answer(texts.DEV_SENT)


@router.callback_query(F.data.startswith("dev:"))
async def dev_moderate(cb: CallbackQuery, bot: Bot):
    if cb.from_user.id != config.owner_id:
        await cb.answer("Только владелец.", show_alert=True)
        return

    _, action, raw_id = cb.data.split(":")
    uid = int(raw_id)
    role = await db.get_role(uid, "dev")
    level = role["level"] if role else "junior"

    if action == "approve":
        await db.upsert_role(uid, "dev", status="active", level=level)
        await cb.message.edit_text(cb.message.html_text + "\n\n✅ Одобрено")
        try:
            await bot.send_message(uid, texts.DEV_APPROVED.format(level=level))
        except Exception:
            pass
    else:
        await db.upsert_role(uid, "dev", status="rejected", level=level)
        await cb.message.edit_text(cb.message.html_text + "\n\n❌ Отклонено")
        try:
            await bot.send_message(uid, texts.DEV_REJECTED)
        except Exception:
            pass

    await cb.answer()