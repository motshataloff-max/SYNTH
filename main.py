import asyncio
import logging
import os
import socket

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import db
from config import config
from handlers import admin, client, common, dev, pr, projects, tester


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


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    await db.init(config.db_path)

    proxy = os.getenv("PROXY_URL", "").strip()
    if proxy:
        session = AiohttpSession(proxy=proxy)
        logging.info("Using proxy: %s", proxy)
    else:
        _patch_dns()
        session = AiohttpSession()
        logging.info("PROXY_URL не задан — использую прямой IP для api.telegram.org")

    bot = Bot(
        config.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(common.router)
    dp.include_router(client.router)
    dp.include_router(dev.router)
    dp.include_router(tester.router)
    dp.include_router(pr.router)
    dp.include_router(projects.router)
    dp.include_router(admin.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())