"""Configuração da aplicação, lida de variáveis de ambiente (e do arquivo .env)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    database_url: str
    timezone: ZoneInfo
    categories_file: Path
    whatsapp_access_token: str
    whatsapp_phone_number_id: str
    whatsapp_app_secret: str
    whatsapp_verify_token: str
    whatsapp_api_version: str

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv(BASE_DIR / ".env")
        categories_file = Path(os.getenv("CATEGORIES_FILE", "config/categorias.json"))
        if not categories_file.is_absolute():
            categories_file = BASE_DIR / categories_file
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite:///./gastos.db"),
            timezone=ZoneInfo(os.getenv("TIMEZONE", "America/Sao_Paulo")),
            categories_file=categories_file,
            whatsapp_access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
            whatsapp_phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
            whatsapp_app_secret=os.getenv("WHATSAPP_APP_SECRET", ""),
            whatsapp_verify_token=os.getenv("WHATSAPP_VERIFY_TOKEN", ""),
            whatsapp_api_version=os.getenv("WHATSAPP_API_VERSION", "v23.0"),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
