import os
from dataclasses import dataclass
from dotenv import load_dotenv


# Загружаем переменные из .env (если файл есть — локальная разработка)
# На Railway .env нет, но переменные уже в os.environ, так что ничего не сломается
load_dotenv()


@dataclass
class Config:
    bot_token: str
    owner_id: int
    bot_username: str
    ping_chat_id: int
    db_path: str


def _load() -> Config:
    """Загружает настройки из переменных окружения."""
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN не задан в переменных окружения")

    owner_id_raw = os.getenv("OWNER_ID", "").strip()
    if not owner_id_raw:
        raise RuntimeError("OWNER_ID не задан в переменных окружения")
    owner_id = int(owner_id_raw)

    bot_username = os.getenv("BOT_USERNAME", "").strip()
    if not bot_username:
        raise RuntimeError("BOT_USERNAME не задан в переменных окружения")

    ping_chat_id_raw = os.getenv("PING_CHAT_ID", "").strip()
    if not ping_chat_id_raw:
        raise RuntimeError("PING_CHAT_ID не задан в переменных окружения")
    ping_chat_id = int(ping_chat_id_raw)

    # Путь к базе данных: на Railway берём из DATA_DIR, локально — "data/bot.db"
    data_dir = os.getenv("DATA_DIR", "data").strip()
    db_path = os.path.join(data_dir, "bot.db")

    return Config(
        bot_token=bot_token,
        owner_id=owner_id,
        bot_username=bot_username,
        ping_chat_id=ping_chat_id,
        db_path=db_path,
    )


# Создаём глобальный объект настроек
config = _load()
