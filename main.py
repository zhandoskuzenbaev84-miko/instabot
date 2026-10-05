import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from handlers.downloader import downloader_router
from handlers.start import start_router

# Log tizimini sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")


async def main():
    """Botni ishga tushirish funksiyasi."""
    # Token tekshiruvi
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "XATO: .env faylida BOT_TOKEN ko'rsatilmagan!\n"
            "Iltimos, @BotFather dan olingan bot tokeningizni .env fayliga kiriting."
        )
        return

    logger.info("Bot ishga tushirilmoqda...")

    # Bot va Dispatcher obyektlarini yaratish
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerlarni ro'yxatdan o'tkazish
    dp.include_router(start_router)
    dp.include_router(downloader_router)

    try:
        # Eski kutilayotgan yangilanishlarni (pending updates) o'chirish
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot muvaffaqiyatli ishga tushdi va xabarlarni qabul qilmoqda!")
        
        # Polling rejimida botni boshlash
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Bot ishlashida xatolik: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot to'xtatildi va sessiya yopildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot foydalanuvchi tomonidan to'xtatildi.")
