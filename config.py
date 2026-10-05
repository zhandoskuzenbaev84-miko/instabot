from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Bot konfiguratsiya sozlamalari (.env fayldan yuklanadi)"""
    BOT_TOKEN: str = "YOUR_BOT_TOKEN_HERE"
    TEMP_DIR: Path = Path("downloads")
    MAX_FILE_SIZE_MB: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Vaqtinchalik yuklab olinadigan fayllar uchun katalog mavjudligini ta'minlash
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
