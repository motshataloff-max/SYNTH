from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import db
import texts
from keyboards import pr_moderation_kb
from states import PRForm
from config import config

router = Router()


def pr_link(user_id: int) -> str:
    return f"https://t.me/{config.bot_username}?start=ref_{user_id}"


@router.message(PRForm.waiting_referrer)
async def pr_referrer(message: Message, state: FSMContext, bot: Bot):
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer("Напишите чуть подробнее, кто вас привёл.")
        return
    await state.clear()

    uid = message.from_user.id
    await db.upsert_role(uid, "pr", status="pending", referrer_text=text[:500])

    owner_text = (
        "📣 <b>Новая заявка на пиарщика</b>\n\n"
        f"ID: <code>{uid}</code>\n"
        f"Имя: {message.from_user.full_name}\n"
        f"Username: @{message.from_user.username or '—'}\n"
        f"Кто привёл: <b>{text[:500]}</b>"
    )
    await bot.send_message(config.owner_id, owner_text,
                           reply_markup=pr_moderation_kb(uid))
    await message.answer(texts.PR_SENT)


@router.callback_query(F.data.startswith("pr:"))
async def pr_moderate(cb: CallbackQuery, bot: Bot):
    if cb.from_user.id != config.owner_id:
        await cb.answer("Только владелец.", show_alert=True)
        return

    _, action, raw_id = cb.data.split(":")
    uid = int(raw_id)

    if action == "approve":
        await db.upsert_role(uid, "pr", status="active")
        await db.set_ref_code(uid, f"ref_{uid}")
        await cb.message.edit_text(cb.message.html_text + "\n\n✅ Одобрено")
        try:
            await bot.send_message(uid, "Ваша заявка одобрена!\n\n" +
                                   texts.PR_LINK_TEXT.format(link=pr_link(uid)))
        except Exception:
            pass
    else:
        await db.upsert_role(uid, "pr", status="rejected")
        await cb.message.edit_text(cb.message.html_text + "\n\n❌ Отклонено")
        try:
            await bot.send_message(uid, texts.PR_REJECTED)
        except Exception:
            pass

    await cb.answer()