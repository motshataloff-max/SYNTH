import asyncio
import logging
import os
import socket
from datetime import datetime
from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

import db
from config import config
from handlers import admin, client, common, dev, pr, projects, tester


# ==========================================
# 1. FLASK ДЛЯ RAILWAY/RENDER (HEALTH CHECK)
# ==========================================
app = Flask(__name__)

@app.route('/')
def health_check():
    """Railway/Render опрашивает этот адрес, чтобы понять, что бот жив."""
    return "Bot is running!", 200

def run_flask():
    """Запускает веб-сервер в отдельном потоке."""
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# ==========================================
# 2. ОБХОД БЛОКИРОВОК (DNS PATCH)
# ==========================================
def _patch_dns() -> None:
    _orig = socket.getaddrinfo

    def _patched(host, port, family=0, type=0, proto=0, flags=0):
        if host == "api.telegram.org":
            return [
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    6,
                    "",
                    ("149.154.167.220", port),
                )
            ]
        return _orig(host, port, family, type, proto, flags)

    socket.getaddrinfo = _patched


# ==========================================
# 3. ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА
# ==========================================
async def main() -> None:
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    
    # Инициализация базы данных
    await db.init(config.db_path)

    # Настройка сети (прокси или прямой IP)
    proxy = os.getenv("PROXY_URL", "").strip()
    if proxy:
        session = AiohttpSession(proxy=proxy)
        logging.info("Using proxy: %s", proxy)
    else:
        _patch_dns()
        session = AiohttpSession()
        logging.info("PROXY_URL не задан — использую прямой IP для api.telegram.org")

    # Создание экземпляра бота и диспетчера
    bot = Bot(
        config.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Подключение всех роутеров (обработчиков команд)
    dp.include_router(common.router)
    dp.include_router(client.router)
    dp.include_router(dev.router)
    dp.include_router(tester.router)
    dp.include_router(pr.router)
    dp.include_router(projects.router)
    dp.include_router(admin.router)

    # Удаление вебхука (на случай, если он был включён ранее)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Настройка всплывающего меню команд (при вводе /)
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота и увидеть меню"),
        BotCommand(command="help", description="❓ Подробная справка по командам"),
        BotCommand(command="stats", description="📊 Общая статистика проекта"),
        BotCommand(command="cancel", description="❌ Отменить текущее действие"),
        BotCommand(command="backup_db", description="💾 Сделать бэкап базы данных"),
        BotCommand(command="restore_db", description="🔄 Восстановить базу из файла"),
    ]
    await bot.set_my_commands(commands)
    logging.info("✅ Меню команд успешно обновлено в Telegram!")

    # Запуск Flask в отдельном потоке (КРИТИЧНО ДЛЯ RAILWAY!)
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("🌐 Flask health check server started")
    
    logging.info("🚀 Bot started successfully!")
    
    # Запуск polling (прослушивание сообщений)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
