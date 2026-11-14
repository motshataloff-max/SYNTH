from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import db
import texts
from keyboards import tester_moderation_kb
from states import TesterForm
from config import config

router = Router()

LEVELS = {"начинающий": "beginner", "опытный": "experienced",
          "beginner": "beginner", "experienced": "experienced"}


@router.message(TesterForm.name)
async def tester_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("Напишите имя.")
        return
    await state.update_data(name=name[:100])
    await state.set_state(TesterForm.level)
    await message.answer(texts.TESTER_ASK_LEVEL)


@router.message(TesterForm.level)
async def tester_level(message: Message, state: FSMContext):
    raw = (message.text or "").strip().lower()
    if raw not in LEVELS:
        await message.answer("Напишите одно слово: Начинающий или Опытный.")
        return
    await state.update_data(level=LEVELS[raw])
    await state.set_state(TesterForm.report)
    await message.answer(texts.TESTER_TASKS[LEVELS[raw]], parse_mode="HTML")


@router.message(TesterForm.report)
async def tester_report(message: Message, state: FSMContext, bot: Bot):
    if not (message.text or message.document):
        await message.answer("Пришлите отчёт текстом или файлом.")
        return

    data = await state.get_data()
    await state.clear()
    uid = message.from_user.id
    level = data["level"]
    name = data["name"]

    await db.upsert_role(uid, "tester", status="pending", level=level)

    owner_text = (
        f"🧪 <b>Заявка тестировщика</b>\n\n"
        f"ID: <code>{uid}</code>\n"
        f"Имя: {name}\n"
        f"Username: @{message.from_user.username or '—'}\n"
        f"Уровень: <b>{level}</b>\n\n"
        f"<b>Отчёт:</b>"
    )
    await bot.send_message(config.owner_id, owner_text,
                           reply_markup=tester_moderation_kb(uid))

    if message.document:
        await bot.send_message(
            config.owner_id,
            f"📎 Файл от <code>{uid}</code>:",
            document=message.document.file_id,
        )
    else:
        text = message.text[:3500]
        await bot.send_message(config.owner_id, f"<pre>{text}</pre>")

    await message.answer(texts.TESTER_SENT)


@router.callback_query(F.data.startswith("tester:"))
async def tester_moderate(cb: CallbackQuery, bot: Bot):
    if cb.from_user.id != config.owner_id:
        await cb.answer("Только владелец.", show_alert=True)
        return

    _, action, raw_id = cb.data.split(":")
    uid = int(raw_id)
    role = await db.get_role(uid, "tester")
    level = role["level"] if role else "beginner"

    if action == "approve":
        await db.upsert_role(uid, "tester", status="active", level=level)
        await cb.message.edit_text(cb.message.html_text + "\n\n✅ Одобрено")
        try:
            await bot.send_message(uid, texts.TESTER_APPROVED.format(level=level))
        except Exception:
            pass
    else:
        await db.upsert_role(uid, "tester", status="rejected", level=level)
        await cb.message.edit_text(cb.message.html_text + "\n\n❌ Отклонено")
        try:
            await bot.send_message(uid, texts.TESTER_REJECTED)
        except Exception:
            pass

    await cb.answer()