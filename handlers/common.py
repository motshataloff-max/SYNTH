from aiogram import Router, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import db
import texts
from keyboards import main_menu, admin_menu
from states import ClientForm, DevForm, PRForm, TesterForm
from config import config

router = Router()


# ---------- Текст команд для разных ролей ----------

USER_COMMANDS = (
    "📌 <b>Что я умею:</b>\n\n"
    "• 🛒 <b>Заказать разработку</b> — оставьте заявку, менеджер свяжется с вами\n"
    "• 👨‍💻 <b>Стать разработчиком</b> — заполните анкету\n"
    "• 🧪 <b>Стать тестировщиком</b> — заполните анкету\n"
    "• 📣 <b>Стать пиарщиком</b> — получите реф-ссылку\n"
    "• 📊 <b>Моя статистика</b> — ваши данные и скидка\n"
    "• ℹ️ <b>О нас</b> — информация о команде\n"
    "• /cancel — сбросить текущее действие\n\n"
    "<i>Нажмите на кнопку внизу экрана 👇</i>"
)

MANAGER_COMMANDS = (
    "📌 <b>Что я умею (менеджер):</b>\n\n"
    "• 📋 <b>Список проектов</b> — все заявки\n"
    "• 👨‍💻 <b>Разработчики</b> — активные разработчики\n"
    "• 🧪 <b>Тестировщики</b> — активные тестеры\n"
    "• 📈 <b>Статистика бота</b> — общая сводка\n"
    "• 🔙 <b>Главное меню</b> — вернуться\n\n"
    "<i>Нажмите на кнопку внизу экрана 👇</i>"
)

BOSS_COMMANDS = (
    "📌 <b>Что я умею (CEO):</b>\n\n"
    "👥 <b>Персонал:</b>\n"
    "• <code>/add_pr &lt;id&gt;</code> — пиарщик\n"
    "• <code>/add_manager &lt;id&gt;</code> — менеджер\n"
    "• <code>/approve_dev &lt;id&gt;</code> — одобрить разработчика\n"
    "• <code>/approve_tester &lt;id&gt;</code> — одобрить тестера\n\n"
    "📊 <b>Статистика:</b>\n"
    "• <code>/stats</code> — общая\n"
    "• <code>/ref_stats &lt;id&gt;</code> — по рефералу\n\n"
    "⚙️ <b>Проекты:</b>\n"
    "• <code>/assign &lt;id&gt;</code> — назначить команду\n"
    "• <code>/complete &lt;id&gt;</code> — завершить проект\n"
    "• <code>/status &lt;id&gt; done|unpaid|new|delete</code>\n\n"
    "💾 <b>База данных:</b>\n"
    "• <code>/backup_db</code> — бэкап в канал\n"
    "• <code>/restore_db</code> — восстановить из файла\n\n"
    "🤖 <b>Бот:</b>\n"
    "• <code>/set_about &lt;текст&gt;</code>\n"
    "• <code>/restart_bot</code>\n"
    "• <code>/bot_status</code>\n\n"
    "<i>Напишите /help для полного списка</i>"
)


# ---------- /start с рефералкой ----------

@router.message(CommandStart(deep_link=True))
async def start_with_link(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    is_owner = uid == config.owner_id
    is_manager = await db.has_active_role(uid, "manager")
    
    ref_code = (command.args or "").strip()
    referrer_id = None
    
    if ref_code.startswith("ref_"):
        referrer_user = await db.find_by_ref_code(ref_code)
        if referrer_user:
            referrer_id = referrer_user["telegram_id"]
    
    await db.get_or_create_user(message.from_user, referrer_id=referrer_id)
    
    if is_owner:
        await message.answer(
            "👑 <b>Добро пожаловать, босс!</b>\n\n" + BOSS_COMMANDS,
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
    elif is_manager:
        await message.answer(
            "💼 <b>Добро пожаловать, менеджер!</b>\n\n" + MANAGER_COMMANDS,
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
    else:
        if referrer_id:
            await message.answer(
                f"🎁 Вы перешли по приглашению от <code>{referrer_id}</code>\n\n" + 
                texts.WELCOME + "\n\n" + USER_COMMANDS,
                reply_markup=main_menu(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                texts.WELCOME + "\n\n" + USER_COMMANDS,
                reply_markup=main_menu(),
                parse_mode="HTML"
            )


# ---------- Обычный /start ----------

@router.message(CommandStart())
async def start_plain(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    is_owner = uid == config.owner_id
    is_manager = await db.has_active_role(uid, "manager")
    
    await db.get_or_create_user(message.from_user)
    
    if is_owner:
        await message.answer(
            "👑 <b>Добро пожаловать, босс!</b>\n\n" + BOSS_COMMANDS,
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
    elif is_manager:
        await message.answer(
            "💼 <b>Добро пожаловать, менеджер!</b>\n\n" + MANAGER_COMMANDS,
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            texts.WELCOME + "\n\n" + USER_COMMANDS,
            reply_markup=main_menu(),
            parse_mode="HTML"
        )


# ---------- /cancel ----------

@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Диалог сброшен.", reply_markup=main_menu())


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
        await message.answer("Ваша заявка на модерации. Менеджер свяжется с вами.")
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
        await message.answer("Ваша заявка на модерации. Менеджер свяжется с вами.")
        return
    await state.set_state(TesterForm.name)
    await message.answer(texts.TESTER_ASK_NAME)


@router.message(F.text == "📣 Стать пиарщиком")
async def menu_pr(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    role = await db.get_role(uid, "pr")
    if role and role["status"] == "active":
        link = f"https://t.me/{config.bot_username}?start=ref_{uid}"
        await message.answer(texts.PR_LINK_TEXT.format(link=link))
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
    is_owner = uid == config.owner_id
    is_manager = await db.has_active_role(uid, "manager")
    
    discount = await db.get_user_discount(uid)
    lines = [
        f"<b>Ваш ID:</b> <code>{uid}</code>",
        f"🎁 <b>Ваша скидка:</b> <b>{discount}%</b> (1% за каждого клиента)"
    ]
    
    if await db.has_active_role(uid, "pr"):
        s = await db.pr_stats(uid)
        link = f"https://t.me/{config.bot_username}?start=ref_{uid}"
        lines += [
            "", "<b>📣 Статистика пиарщика:</b>",
            f"Ссылка: {link}",
            f"Клиентов: <b>{s['clients']}</b>",
            f"Заказов: <b>{s['orders']}</b>",
            f"Оборот: <b>{s['total']} ⭐</b>",
        ]
    
    if is_owner or is_manager:
        await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=admin_menu())
    else:
        await message.answer("\n".join(lines), parse_mode="HTML")


# ---------- Админ-кнопки ----------

@router.message(F.text == "🔙 Главное меню")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu())


@router.message(F.text == "📈 Статистика бота")
async def admin_stats_button(message: Message):
    uid = message.from_user.id
    if not (uid == config.owner_id or await db.has_active_role(uid, "manager")):
        return
    s = await db.general_stats()
    lines = [
        "<b>📊 Общая статистика</b>",
        "──────────────────────",
        f"👥 Пользователей: <b>{s.get('clients', 0)}</b>",
        f"👨‍💻 Senior: <b>{s.get('devs', {}).get('senior', 0)}</b>",
        f"👨‍💻 Medium: <b>{s.get('devs', {}).get('medium', 0)}</b>",
        f"👨‍💻 Junior: <b>{s.get('devs', {}).get('junior', 0)}</b>",
        f"🧪 Начинающие: <b>{s.get('testers', {}).get('beginner', 0)}</b>",
        f"🧪 Опытные: <b>{s.get('testers', {}).get('experienced', 0)}</b>",
        "──────────────────────",
        f"📦 Активных: <b>{s.get('active_projects', 0)}</b>",
        f"✅ Завершённых: <b>{s.get('done_projects', 0)}</b>",
        f"💰 Оборот: <b>{s.get('turnover', 0)} ⭐</b>",
        f"🏦 Счёт компании: <b>{s.get('company', 0)} ⭐</b>",
    ]
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "📋 Список проектов")
async def admin_projects_button(message: Message):
    uid = message.from_user.id
    if not (uid == config.owner_id or await db.has_active_role(uid, "manager")):
        return
    rows = await db.list_projects(limit=20)
    if not rows:
        await message.answer("📭 Проектов нет.")
        return
    lines = ["<b>📋 Проекты:</b>"]
    for r in rows:
        emoji = {"new": "🆕", "assigned": "👥", "in_progress": "🔨", "done": "✅"}.get(r["status"], "⚪")
        lines.append(f"{emoji} #{r['id']} | <b>{r['budget']}⭐</b> | {r['status']} | {r['title'][:30]}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "👥 Менеджеры")
async def admin_managers_button(message: Message):
    if message.from_user.id != config.owner_id:
        return
    rows = await db.list_managers()
    if not rows:
        await message.answer("📭 Менеджеров нет.")
        return
    lines = ["<b>👥 Менеджеры:</b>"]
    for r in rows:
        emoji = {"active": "🟢", "suspended": "🟡", "rejected": "🔴"}.get(r.get("status"), "⚪")
        lines.append(f"{emoji} <code>{r['telegram_id']}</code> — {r['status']}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "👨‍💻 Разработчики")
async def admin_devs_button(message: Message):
    uid = message.from_user.id
    if not (uid == config.owner_id or await db.has_active_role(uid, "manager")):
        return
    devs = await db.list_active_by_role("dev")
    if not devs:
        await message.answer("📭 Разработчиков нет.")
        return
    lines = ["<b>👨‍💻 Разработчики:</b>"]
    for d in devs:
        lines.append(f"• <code>{d['telegram_id']}</code> — {d['level']}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "🧪 Тестировщики")
async def admin_testers_button(message: Message):
    uid = message.from_user.id
    if not (uid == config.owner_id or await db.has_active_role(uid, "manager")):
        return
    testers = await db.list_active_by_role("tester")
    if not testers:
        await message.answer("📭 Тестировщиков нет.")
        return
    lines = ["<b>🧪 Тестировщики:</b>"]
    for t in testers:
        lines.append(f"• <code>{t['telegram_id']}</code> — {t['level']}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "⚙️ Настройки")
async def admin_settings_button(message: Message):
    if message.from_user.id != config.owner_id:
        return
    await message.answer(
        "<b>⚙️ Настройки</b>\n\n"
        "• <code>/set_about &lt;текст&gt;</code>\n"
        "• <code>/add_manager &lt;id&gt;</code>\n"
        "• <code>/add_pr &lt;id&gt;</code>\n"
        "• <code>/backup_db</code> — бэкап БД\n"
        "• <code>/restart_bot</code>",
        parse_mode="HTML"
    )
