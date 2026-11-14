import os
import sys
import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, FSInputFile

import db
from config import config
from keyboards import main_menu

logger = logging.getLogger(__name__)
router = Router()

class AdminRestoreState(StatesGroup):
    waiting_for_file = State()


def is_owner(message: Message) -> bool:
    return message.from_user.id == config.owner_id


def extract_user_id(message: Message) -> int | None:
    parts = message.text.split()
    if len(parts) < 2:
        return None
    if parts[1].isdigit():
        return int(parts[1])
    return None


# ==========================================
# 1. ТЕКСТОВЫЕ КОМАНДЫ И ТРИГГЕРЫ
# ==========================================

@router.message(Command("help"))
async def cmd_help(message: Message):
    if not is_owner(message):
        await message.answer("👋 Эта команда доступна только владельцу.")
        return
    help_text = (
        "👑 <b>Команды владельца (CEO):</b>\n\n"
        "👥 <b>Персонал:</b>\n"
        "• <code>/add_pr &lt;id&gt;</code> — пиарщик\n"
        "• <code>/add_manager &lt;id&gt;</code> — менеджер\n"
        "• <code>/remove_manager &lt;id&gt;</code> — уволить\n"
        "• <code>/suspend_manager &lt;id&gt;</code> — отстранить\n"
        "• <code>/resume_manager &lt;id&gt;</code> — вернуть\n"
        "• <code>/list_managers</code> — список\n\n"
        "✅ <b>Модерация:</b>\n"
        "• <code>/approve_dev &lt;id&gt;</code> / <code>/reject_dev &lt;id&gt;</code>\n"
        "• <code>/approve_tester &lt;id&gt;</code> / <code>/reject_tester &lt;id&gt;</code>\n\n"
        "📊 <b>Статистика:</b>\n"
        "• <code>/stats</code> — общая\n"
        "• <code>/ref_stats &lt;id&gt;</code> — по рефералу\n\n"
        "💾 <b>База данных:</b>\n"
        "• <code>/backup_db</code> — отправить бэкап в канал\n"
        "• <code>/restore_db</code> — восстановить из файла\n\n"
        "🤖 <b>Бот:</b>\n"
        "• <code>/set_about &lt;текст&gt;</code>\n"
        "• <code>/restart_bot</code>"
    )
    await message.answer(help_text, parse_mode="HTML")


@router.message(F.text.lower().in_(["завершить", "завершено", "комплит", "complete", "закрыть"]))
async def hint_complete(message: Message):
    if not is_owner(message): return
    await message.answer(
        "✅ <b>Как завершить проект:</b>\n\n"
        "<code>/complete &lt;project_id&gt;</code>\n\n"
        "<i>Бот распределит Stars и начислит рефереру +1% к скидке.</i>",
        parse_mode="HTML"
    )


@router.message(F.text.lower().in_(["отменить", "отмена", "cancel"]))
async def hint_cancel(message: Message):
    await message.answer("❌ <b>Как отменить действие:</b>\n\n<code>/cancel</code>", parse_mode="HTML")


# ---------- Настройки и Персонал ----------

@router.message(Command("set_about"))
async def set_about(message: Message):
    if not is_owner(message): return
    text = message.text.partition(" ")[2].strip()
    if not text:
        return await message.answer("⚠️ <code>/set_about новый текст</code>", parse_mode="HTML")
    try:
        await db.set_setting("about", text)
        await message.answer("✅ Текст «О нас» обновлён!")
    except Exception as e:
        logger.error(f"Ошибка set_about: {e}")
        await message.answer("❌ Ошибка БД.")


@router.message(Command("add_pr"))
async def add_pr(message: Message):
    if not is_owner(message): return
    uid = extract_user_id(message)
    if not uid:
        return await message.answer("⚠️ <code>/add_pr &lt;id&gt;</code>", parse_mode="HTML")
    try:
        ref_code = f"ref_{uid}"
        await db.upsert_role(uid, "pr", status="active")
        await db.set_ref_code(uid, ref_code)
        await message.answer(f"✅ <code>{uid}</code> — пиарщик!\n🔗 Ссылка: <code>https://t.me/{config.bot_username}?start={ref_code}</code>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка add_pr: {e}")
        await message.answer("❌ Ошибка БД.")


@router.message(Command("add_manager"))
async def add_manager(message: Message):
    if not is_owner(message): return
    uid = extract_user_id(message)
    if not uid: return await message.answer("⚠️ <code>/add_manager &lt;id&gt;</code>", parse_mode="HTML")
    try:
        await db.upsert_role(uid, "manager", status="active")
        await message.answer(f"✅ <code>{uid}</code> — менеджер.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка add_manager: {e}")
        await message.answer("❌ Ошибка БД.")


@router.message(Command("remove_manager"))
async def remove_manager(message: Message):
    if not is_owner(message): return
    uid = extract_user_id(message)
    if not uid: return await message.answer("⚠️ <code>/remove_manager &lt;id&gt;</code>", parse_mode="HTML")
    try:
        await db.upsert_role(uid, "manager", status="rejected")
        await message.answer(f"🗑 <code>{uid}</code> уволен.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка remove_manager: {e}")
        await message.answer("❌ Ошибка БД.")


@router.message(Command("suspend_manager"))
async def suspend_manager(message: Message):
    if not is_owner(message): return
    uid = extract_user_id(message)
    if not uid: return await message.answer("⚠️ <code>/suspend_manager &lt;id&gt;</code>", parse_mode="HTML")
    try:
        await db.upsert_role(uid, "manager", status="suspended")
        await message.answer(f"⏸ <code>{uid}</code> отстранён.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка suspend_manager: {e}")
        await message.answer("❌ Ошибка БД.")


@router.message(Command("resume_manager"))
async def resume_manager(message: Message):
    if not is_owner(message): return
    uid = extract_user_id(message)
    if not uid: return await message.answer("⚠️ <code>/resume_manager &lt;id&gt;</code>", parse_mode="HTML")
    try:
        await db.upsert_role(uid, "manager", status="active")
        await message.answer(f"▶️ <code>{uid}</code> возвращён.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка resume_manager: {e}")
        await message.answer("❌ Ошибка БД.")


@router.message(Command("list_managers"))
async def list_managers(message: Message):
    if not is_owner(message): return
    try:
        rows = await db.list_managers()
        if not rows: return await message.answer("📭 Менеджеров нет.")
        lines = ["<b>📋 Менеджеры:</b>"]
        for r in rows:
            emoji = {"active": "🟢", "suspended": "🟡", "rejected": "🔴"}.get(r.get("status"), "⚪")
            lines.append(f"{emoji} <code>{r['telegram_id']}</code> — {r['status']}")
        await message.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка list_managers: {e}")
        await message.answer("❌ Ошибка БД.")


# ---------- Модерация ----------

@router.message(Command("approve_dev"))
async def approve_dev(message: Message):
    if not is_owner(message): return
    uid = extract_user_id(message)
    if not uid: return await message.answer("⚠️ <code>/approve_dev &lt;id&gt;</code>", parse_mode="HTML")
    try:
        role = await db.get_role(uid, "dev")
        level = role["level"] if role else "junior"
        await db.upsert_role(uid, "dev", status="active", level=level)
        await message.answer(f"✅ <code>{uid}</code> одобрен ({level}).", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка approve_dev: {e}")
        await message.answer("❌ Ошибка БД.")

@router.message(Command("reject_dev"))
async def reject_dev(message: Message):
    if not is_owner(message): return
    uid = extract_user_id(message)
    if not uid: return await message.answer("⚠️ <code>/reject_dev &lt;id&gt;</code>", parse_mode="HTML")
    try:
        await db.upsert_role(uid, "dev", status="rejected")
        await message.answer(f"❌ <code>{uid}</code> отклонён.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка reject_dev: {e}")
        await message.answer("❌ Ошибка БД.")

@router.message(Command("approve_tester"))
async def approve_tester(message: Message):
    if not is_owner(message): return
    uid = extract_user_id(message)
    if not uid: return await message.answer("⚠️ <code>/approve_tester &lt;id&gt;</code>", parse_mode="HTML")
    try:
        role = await db.get_role(uid, "tester")
        level = role["level"] if role else "beginner"
        await db.upsert_role(uid, "tester", status="active", level=level)
        await message.answer(f"✅ <code>{uid}</code> одобрен ({level}).", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка approve_tester: {e}")
        await message.answer("❌ Ошибка БД.")

@router.message(Command("reject_tester"))
async def reject_tester(message: Message):
    if not is_owner(message): return
    uid = extract_user_id(message)
    if not uid: return await message.answer("⚠️ <code>/reject_tester &lt;id&gt;</code>", parse_mode="HTML")
    try:
        await db.upsert_role(uid, "tester", status="rejected")
        await message.answer(f"❌ <code>{uid}</code> отклонён.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка reject_tester: {e}")
        await message.answer("❌ Ошибка БД.")


# ---------- Статистика ----------

@router.message(Command("stats"))
async def stats(message: Message):
    if not is_owner(message): return
    try:
        s = await db.general_stats()
        lines = [
            "<b>📊 Общая статистика</b>", "──────────────────────",
            f"👥 Пользователей: <b>{s.get('clients', 0)}</b>",
            f"👨‍💻 Devs: Sr <b>{s.get('devs', {}).get('senior', 0)}</b>, Md <b>{s.get('devs', {}).get('medium', 0)}</b>, Jr <b>{s.get('devs', {}).get('junior', 0)}</b>",
            f"🧪 Testers: Beg <b>{s.get('testers', {}).get('beginner', 0)}</b>, Exp <b>{s.get('testers', {}).get('experienced', 0)}</b>",
            "──────────────────────",
            f"📦 Активных: <b>{s.get('active_projects', 0)}</b>", f"✅ Завершённых: <b>{s.get('done_projects', 0)}</b>",
            f"💰 Оборот: <b>{s.get('turnover', 0)} ⭐</b>", f"🏦 Счёт компании: <b>{s.get('company', 0)} ⭐</b>",
        ]
        await message.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка stats: {e}")
        await message.answer("❌ Ошибка БД.")

@router.message(Command("ref_stats"))
async def ref_stats(message: Message):
    if not is_owner(message): return
    parts = message.text.split()
    if len(parts) < 2: return await message.answer("⚠️ <code>/ref_stats &lt;id&gt;</code>", parse_mode="HTML")
    ref_id = parts[1]
    try:
        s = await db.ref_stats(int(ref_id) if ref_id.isdigit() else ref_id)
        lines = [
            f"<b>🔗 Реферал: <code>{ref_id}</code></b>", "──────────────────────",
            f"👥 Клиентов: <b>{s.get('clients', 0)}</b>", f"📝 Заказов: <b>{s.get('orders', 0)}</b>",
            f"💵 Оборот: <b>{s.get('total', 0)} ⭐</b>", f"💰 Начислено: <b>{s.get('earned', 0)} ⭐</b>",
        ]
        await message.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка ref_stats: {e}")
        await message.answer("❌ Ошибка БД.")


# ---------- Управление ботом ----------

@router.message(Command("restart_bot"))
async def restart_bot(message: Message):
    if not is_owner(message): return
    await message.answer("🔄 <b>Перезапуск...</b>", parse_mode="HTML")
    os.execv(sys.executable, [sys.executable] + sys.argv)


# ==========================================
# 2. ОБРАБОТЧИКИ INLINE-КНОПОК (Callback)
# ==========================================

@router.callback_query(F.data.startswith("dev_approve_"))
async def callback_dev_approve(callback: CallbackQuery):
    if not is_owner(callback.message): return await callback.answer("⛔ Доступ запрещён", show_alert=True)
    user_id = int(callback.data.split("_")[2])
    try:
        role = await db.get_role(user_id, "dev")
        level = role["level"] if role else "junior"
        await db.upsert_role(user_id, "dev", status="active", level=level)
        await callback.message.edit_text(f"✅ <code>{user_id}</code> одобрен как разработчик ({level}).", parse_mode="HTML")
        await callback.answer("Одобрено!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.answer("❌ Ошибка БД", show_alert=True)

@router.callback_query(F.data.startswith("dev_reject_"))
async def callback_dev_reject(callback: CallbackQuery):
    if not is_owner(callback.message): return await callback.answer("⛔ Доступ запрещён", show_alert=True)
    user_id = int(callback.data.split("_")[2])
    try:
        await db.upsert_role(user_id, "dev", status="rejected")
        await callback.message.edit_text(f"❌ <code>{user_id}</code> отклонён.", parse_mode="HTML")
        await callback.answer("Отклонено!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.answer("❌ Ошибка БД", show_alert=True)

@router.callback_query(F.data.startswith("tester_approve_"))
async def callback_tester_approve(callback: CallbackQuery):
    if not is_owner(callback.message): return await callback.answer("⛔ Доступ запрещён", show_alert=True)
    user_id = int(callback.data.split("_")[2])
    try:
        role = await db.get_role(user_id, "tester")
        level = role["level"] if role else "beginner"
        await db.upsert_role(user_id, "tester", status="active", level=level)
        await callback.message.edit_text(f"✅ <code>{user_id}</code> одобрен как тестировщик ({level}).", parse_mode="HTML")
        await callback.answer("Одобрено!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.answer("❌ Ошибка БД", show_alert=True)

@router.callback_query(F.data.startswith("tester_reject_"))
async def callback_tester_reject(callback: CallbackQuery):
    if not is_owner(callback.message): return await callback.answer("⛔ Доступ запрещён", show_alert=True)
    user_id = int(callback.data.split("_")[2])
    try:
        await db.upsert_role(user_id, "tester", status="rejected")
        await callback.message.edit_text(f"❌ <code>{user_id}</code> отклонён.", parse_mode="HTML")
        await callback.answer("Отклонено!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.answer("❌ Ошибка БД", show_alert=True)

@router.callback_query(F.data.startswith("pr_approve_"))
async def callback_pr_approve(callback: CallbackQuery):
    if not is_owner(callback.message): return await callback.answer("⛔ Доступ запрещён", show_alert=True)
    user_id = int(callback.data.split("_")[2])
    try:
        ref_code = f"ref_{user_id}"
        await db.upsert_role(user_id, "pr", status="active")
        await db.set_ref_code(user_id, ref_code)
        await callback.message.edit_text(f"✅ <code>{user_id}</code> — пиарщик!\n🔗 Ссылка: <code>https://t.me/{config.bot_username}?start={ref_code}</code>", parse_mode="HTML")
        await callback.answer("Одобрено!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.answer("❌ Ошибка БД", show_alert=True)

@router.callback_query(F.data.startswith("pr_reject_"))
async def callback_pr_reject(callback: CallbackQuery):
    if not is_owner(callback.message): return await callback.answer("⛔ Доступ запрещён", show_alert=True)
    user_id = int(callback.data.split("_")[2])
    try:
        await db.upsert_role(user_id, "pr", status="rejected")
        await callback.message.edit_text(f"❌ <code>{user_id}</code> отклонён.", parse_mode="HTML")
        await callback.answer("Отклонено!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.answer("❌ Ошибка БД", show_alert=True)


# ==========================================
# 3. УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК КНОПОК
# ==========================================

@router.callback_query()
async def universal_callback(callback: CallbackQuery):
    data = callback.data
    is_owner_check = callback.from_user.id == config.owner_id
    
    if data.startswith("proj_assign_"):
        if not is_owner_check: return await callback.answer("⛔ Только CEO", show_alert=True)
        project_id = data.split("_")[2]
        await callback.answer()
        await callback.message.answer(f"⚙️ Назначение на проект #{project_id}\n\nИспользуй: <code>/assign {project_id}</code>", parse_mode="HTML")
    elif data.startswith("proj_complete_"):
        if not is_owner_check: return await callback.answer("⛔ Только CEO", show_alert=True)
        project_id = data.split("_")[2]
        await callback.answer()
        await callback.message.answer(f"✅ Завершение проекта #{project_id}\n\nИспользуй: <code>/complete {project_id}</code>", parse_mode="HTML")
    elif data.startswith("proj_unpaid_"):
        if not is_owner_check: return await callback.answer("⛔ Только CEO", show_alert=True)
        project_id = data.split("_")[2]
        await callback.answer()
        await callback.message.answer(f"💸 Пометка проекта #{project_id}\n\nИспользуй: <code>/status {project_id} unpaid</code>", parse_mode="HTML")
    elif data.startswith("proj_cancel_"):
        if not is_owner_check: return await callback.answer("⛔ Только CEO", show_alert=True)
        project_id = data.split("_")[2]
        await callback.answer()
        await callback.message.answer(f"❌ Отмена проекта #{project_id}\n\nИспользуй: <code>/status {project_id} delete</code>", parse_mode="HTML")
    elif data == "back_to_menu":
        await callback.answer()
        await callback.message.answer("Возвращаемся в главное меню:", reply_markup=main_menu())
    else:
        await callback.answer()
        if is_owner_check:
            await callback.message.answer(f"🤔 Неизвестная кнопка: <code>{data}</code>", parse_mode="HTML")


# ==========================================
# 4. РЕЗЕРВНОЕ КОПИРОВАНИЕ И ВОССТАНОВЛЕНИЕ
# ==========================================

@router.message(Command("backup_db"))
async def backup_db(message: Message):
    if not is_owner(message): return
    db_path = db.DB_PATH
    if not os.path.exists(db_path):
        return await message.answer("❌ Файл базы данных не найден.")
    try:
        await message.answer("⏳ Отправляю базу данных в канал...")
        doc = FSInputFile(db_path)
        await message.bot.send_document(
            chat_id=config.ping_chat_id,
            document=doc,
            caption=f"📦 <b>Бэкап БД</b>\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await message.answer("✅ База данных успешно отправлена в канал!")
    except Exception as e:
        logger.error(f"Ошибка отправки бэкапа: {e}")
        await message.answer(f"❌ Ошибка при отправке: {e}")


@router.message(Command("restore_db"))
async def restore_db_start(message: Message, state: FSMContext):
    if not is_owner(message): return
    await state.set_state(AdminRestoreState.waiting_for_file)
    await message.answer("📥 <b>Режим восстановления активирован.</b>\n\nПерешли мне файл <code>.db</code> из канала или напиши /cancel.")


@router.message(AdminRestoreState.waiting_for_file, F.document)
async def restore_db_process(message: Message, state: FSMContext, bot: Bot):
    if not is_owner(message): return
    doc = message.document
    if not doc.file_name or not doc.file_name.endswith(".db"):
        return await message.answer("❌ Это не файл .db. Попробуй снова или /cancel.")
    
    await message.answer("⏳ Скачиваю и восстанавливаю базу... Не выключай бота.")
    try:
        file = await bot.get_file(doc.file_id)
        target_path = db.DB_PATH
        os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
        await bot.download_file(file.file_path, target_path)
        await state.clear()
        await message.answer(f"✅ База <code>{doc.file_name}</code> восстановлена!\n\n🔄 Перезапускаю бота...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        logger.error(f"Ошибка восстановления БД: {e}")
        await state.clear()
        await message.answer(f"❌ Ошибка: {e}")


@router.message(AdminRestoreState.waiting_for_file, Command("cancel"))
async def cancel_restore(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Восстановление отменено.", reply_markup=main_menu())
