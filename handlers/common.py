from aiogram import Router, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import db
import texts
from keyboards import main_menu
from states import ClientForm, DevForm, PRForm, TesterForm
from config import config

router = Router()


@router.message(CommandStart(deep_link=True))
async def start_with_link(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    ref_code = (command.args or "").strip()
    referrer_id = None
    if ref_code.startswith("ref_"):
        u = await db.find_by_ref_code(ref_code)
        if u:
            referrer_id = u["telegram_id"]
    await db.get_or_create_user(message.from_user, referrer_id=referrer_id)
    await message.answer(texts.WELCOME, reply_markup=main_menu())


@router.message(CommandStart())
async def start_plain(message: Message, state: FSMContext):
    await state.clear()
    await db.get_or_create_user(message.from_user)
    await message.answer(texts.WELCOME, reply_markup=main_menu())


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Диалог сброшен. Выберите действие в меню.", reply_markup=main_menu())


# ---------- Кнопки меню ----------

@router.message(F.text == "🛒 Заказать разработку")
async def menu_order(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ClientForm.title)
    await message.answer("Как вас зовут или как называется проект? (одна строка)")


@router.message(F.text == "👨‍💻 Стать разработчиком")
async def menu_dev(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    role = await db.get_role(uid, "dev")
    if role and role["status"] == "active":
        await message.answer(f"Вы уже разработчик. Уровень: <b>{role['level']}</b>.")
        return
    if role and role["status"] == "pending":
        await message.answer("Ваша заявка на разработчика на модерации.")
        return
    await state.set_state(DevForm.name)
    await message.answer(texts.DEV_ASK_NAME)


@router.message(F.text == "🧪 Стать тестировщиком")
async def menu_tester(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    role = await db.get_role(uid, "tester")
    if role and role["status"] == "active":
        await message.answer(f"Вы уже тестировщик. Уровень: <b>{role['level']}</b>.")
        return
    if role and role["status"] == "pending":
        await message.answer("Ваша заявка на тестировщика на модерации.")
        return
    await state.set_state(TesterForm.name)
    await message.answer(texts.TESTER_ASK_NAME)


@router.message(F.text == "📣 Стать пиарщиком")
async def menu_pr(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    role = await db.get_role(uid, "pr")
    if role and role["status"] == "active":
        await message.answer(texts.PR_LINK_TEXT.format(
            link=f"https://t.me/{config.bot_username}?start=ref_{uid}"))
        return
    if role and role["status"] == "pending":
        await message.answer(texts.PR_PENDING)
        return
    if role and role["status"] == "rejected":
        await message.answer(texts.PR_REJECTED)
        return
    await state.set_state(PRForm.waiting_referrer)
    await message.answer(texts.PR_ASK_REFERRER)


@router.message(F.text == "ℹ️ О нас")
async def about(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(await db.get_setting("about"))


@router.message(F.text == "📊 Моя статистика")
async def my_stats(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    lines = [f"<b>Ваш ID:</b> <code>{uid}</code>"]

    if await db.has_active_role(uid, "pr"):
        s = await db.pr_stats(uid)
        link = f"https://t.me/{config.bot_username}?start=ref_{uid}"
        lines += [
            "",
            "<b>📣 Пиарщик</b>",
            f"Реф-ссылка: {link}",
            f"Приведено клиентов: <b>{s['clients']}</b>",
            f"Заказов от них: <b>{s['orders']}</b>",
            f"Оборот: <b>{s['total']} ⭐</b>",
            f"Начислено вам: <b>{s['earned']} ⭐</b>",
        ]

    if len(lines) == 1:
        lines.append("\nПока у вас нет активных ролей.")
    await message.answer("\n".join(lines))