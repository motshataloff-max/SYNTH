import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    owner_id: int
    bot_username: str
    db_path: str = "data/bot.db"


def _load() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    owner_raw = os.getenv("OWNER_ID", "0")
    username = os.getenv("BOT_USERNAME", "").strip().lstrip("@")
    db_path = os.getenv("DB_PATH", "data/bot.db").strip()

    if not token:
        raise RuntimeError("BOT_TOKEN не задан в .env")
    if not owner_raw.isdigit() or int(owner_raw) == 0:
        raise RuntimeError("OWNER_ID должен быть числом в .env")
    if not username:
        raise RuntimeError("BOT_USERNAME обязателен (для реф-ссылок)")

    return Config(
        bot_token=token,
        owner_id=int(owner_raw),
        bot_username=username,
        db_path=db_path,
    )


config = _load()