import os
import sys

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import db
from config import config

router = Router()


def owner_only(message: Message) -> bool:
    return message.from_user.id == config.owner_id


def _uid_from(message: Message):
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return int(parts[1])


@router.message(Command("set_about"))
async def set_about(message: Message):
    if not owner_only(message):
        return
    text = message.text.partition(" ")[2].strip()
    if not text:
        await message.answer("Использование: <code>/set_about новый текст</code>")
        return
    await db.set_setting("about", text)
    await message.answer("✅ Текст «О нас» обновлён.")


@router.message(Command("add_pr"))
async def add_pr(message: Message):
    if not owner_only(message):
        return
    uid = _uid_from(message)
    if not uid:
        await message.answer("Использование: <code>/add_pr &lt;user_id&gt;</code>")
        return
    await db.upsert_role(uid, "pr", status="active")
    await db.set_ref_code(uid, f"ref_{uid}")
    await message.answer(f"✅ {uid} теперь пиарщик. Ссылка: "
                         f"https://t.me/{config.bot_username}?start=ref_{uid}")


# ---------- managers ----------

@router.message(Command("add_manager"))
async def add_manager(message: Message):
    if not owner_only(message):
        return
    uid = _uid_from(message)
    if not uid:
        await message.answer("Использование: <code>/add_manager &lt;user_id&gt;</code>")
        return
    await db.upsert_role(uid, "manager", status="active")
    await message.answer(f"✅ {uid} назначен менеджером.")


@router.message(Command("remove_manager"))
async def remove_manager(message: Message):
    if not owner_only(message):
        return
    uid = _uid_from(message)
    if not uid:
        await message.answer("Использование: <code>/remove_manager &lt;user_id&gt;</code>")
        return
    await db.upsert_role(uid, "manager", status="rejected")
    await message.answer(f"🗑 {uid} снят с менеджеров.")


@router.message(Command("suspend_manager"))
async def suspend_manager(message: Message):
    if not owner_only(message):
        return
    uid = _uid_from(message)
    if not uid:
        await message.answer("Использование: <code>/suspend_manager &lt;user_id&gt;</code>")
        return
    await db.upsert_role(uid, "manager", status="suspended")
    await message.answer(f"⏸ {uid} временно отстранён.")


@router.message(Command("resume_manager"))
async def resume_manager(message: Message):
    if not owner_only(message):
        return
    uid = _uid_from(message)
    if not uid:
        await message.answer("Использование: <code>/resume_manager &lt;user_id&gt;</code>")
        return
    await db.upsert_role(uid, "manager", status="active")
    await message.answer(f"▶️ {uid} возвращён к работе.")


@router.message(Command("list_managers"))
async def list_managers(message: Message):
    if not owner_only(message):
        return
    rows = await db.list_managers()
    if not rows:
        await message.answer("Менеджеров пока нет.")
        return
    lines = ["<b>Менеджеры:</b>"]
    for r in rows:
        lines.append(f"• <code>{r['telegram_id']}</code> — {r['status']}")
    await message.answer("\n".join(lines))


# ---------- dev/tester approval ----------

@router.message(Command("approve_dev"))
async def approve_dev(message: Message):
    if not owner_only(message):
        return
    uid = _uid_from(message)
    if not uid:
        await message.answer("Использование: <code>/approve_dev &lt;user_id&gt;</code>")
        return
    role = await db.get_role(uid, "dev")
    level = role["level"] if role else "junior"
    await db.upsert_role(uid, "dev", status="active", level=level)
    await message.answer(f"✅ {uid} одобрен как разработчик ({level}).")


@router.message(Command("reject_dev"))
async def reject_dev(message: Message):
    if not owner_only(message):
        return
    uid = _uid_from(message)
    if not uid:
        await message.answer("Использование: <code>/reject_dev &lt;user_id&gt;</code>")
        return
    role = await db.get_role(uid, "dev")
    level = role["level"] if role else None
    await db.upsert_role(uid, "dev", status="rejected", level=level)
    await message.answer(f"❌ {uid} отклонён как разработчик.")


@router.message(Command("approve_tester"))
async def approve_tester(message: Message):
    if not owner_only(message):
        return
    uid = _uid_from(message)
    if not uid:
        await message.answer("Использование: <code>/approve_tester &lt;user_id&gt;</code>")
        return
    role = await db.get_role(uid, "tester")
    level = role["level"] if role else "beginner"
    await db.upsert_role(uid, "tester", status="active", level=level)
    await message.answer(f"✅ {uid} одобрен как тестировщик ({level}).")


@router.message(Command("reject_tester"))
async def reject_tester(message: Message):
    if not owner_only(message):
        return
    uid = _uid_from(message)
    if not uid:
        await message.answer("Использование: <code>/reject_tester &lt;user_id&gt;</code>")
        return
    role = await db.get_role(uid, "tester")
    level = role["level"] if role else None
    await db.upsert_role(uid, "tester", status="rejected", level=level)
    await message.answer(f"❌ {uid} отклонён как тестировщик.")


# ---------- stats ----------

@router.message(Command("stats"))
async def stats(message: Message):
    if not owner_only(message):
        return
    s = await db.general_stats()
    lines = [
        "<b>📊 Общая статистика</b>",
        "",
        f"Пользователей: <b>{s['clients']}</b>",
        f"Разработчики: Senior <b>{s['devs']['senior']}</b>, "
        f"Medium <b>{s['devs']['medium']}</b>, Junior <b>{s['devs']['junior']}</b>",
        f"Тестировщики: Начинающие <b>{s['testers']['beginner']}</b>, "
        f"Опытные <b>{s['testers']['experienced']}</b>",
        f"Активных проектов: <b>{s['active_projects']}</b>",
        f"Завершённых проектов: <b>{s['done_projects']}</b>",
        f"Общий оборот: <b>{s['turnover']} ⭐</b>",
        f"Счёт компании: <b>{s['company']} ⭐</b>",
    ]
    await message.answer("\n".join(lines))


@router.message(Command("ref_stats"))
async def ref_stats(message: Message):
    if not owner_only(message):
        return
    uid = _uid_from(message)
    if not uid:
        await message.answer("Использование: <code>/ref_stats &lt;ref_id&gt;</code>")
        return
    s = await db.ref_stats(uid)
    lines = [
        f"<b>Реферал <code>{uid}</code></b>",
        "",
        f"Приведено клиентов: <b>{s['clients']}</b>",
        f"Заказов от них: <b>{s['orders']}</b>",
        f"На общую сумму: <b>{s['total']} ⭐</b>",
        f"Начислено как пиарщику: <b>{s['earned']} ⭐</b>",
        f"Приведённых сотрудников: <b>{s['staff']}</b>",
    ]
    await message.answer("\n".join(lines))


# ---------- bot control ----------

@router.message(Command("bot_status"))
async def bot_status(message: Message):
    if not owner_only(message):
        return
    await message.answer("🟢 Бот работает. Polling активен.")


@router.message(Command("stop_bot"))
async def stop_bot(message: Message):
    if not owner_only(message):
        return
    await message.answer("🔴 Останавливаю бота.")
    sys.exit(0)


@router.message(Command("restart_bot"))
async def restart_bot(message: Message):
    if not owner_only(message):
        return
    await message.answer("🔄 Перезапускаю бота...")
    os.execv(sys.executable, [sys.executable] + sys.argv)