import asyncio
import logging
import os
import sys
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from handlers.downloader import downloader_router
from handlers.start import start_router

# Mahalliy bin papkasini (agar mavjud bo'lsa, masalan Render Native FFmpeg) PATH ga qo'shish
local_bin = (Path(__file__).parent / "bin").resolve()
if local_bin.exists():
    path_sep = ";" if sys.platform == "win32" else ":"
    os.environ["PATH"] = f"{local_bin}{path_sep}{os.environ.get('PATH', '')}"

# Log tizimini sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")


async def start_dummy_health_server():
    """
    Render yoki shunga o'xshash bulutli platformalarda Web Service port skanerlashini
    qondirish uchun yengil HTTP server (PORT muhit o'zgaruvchisi berilgan bo'lsa ishlaydi).
    """
    port_env = os.environ.get("PORT")
    if not port_env:
        return None

    try:
        port = int(port_env)
        app = web.Application()

        async def health_check(_):
            return web.Response(text="Bot is running! Status: OK")

        app.router.add_get("/", health_check)
        app.router.add_get("/health", health_check)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Render Web Service salomatlik tekshiruvi serveri 0.0.0.0:{port} da ishga tushdi.")
        return runner
    except Exception as e:
        logger.warning(f"Health serverni ishga tushirishda xatolik: {e}")
        return None


async def main():
    """Botni ishga tushirish funksiyasi."""
    # Token tekshiruvi
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "XATO: .env faylida yoki Render Environment Variables'da BOT_TOKEN ko'rsatilmagan!\n"
            "Iltimos, @BotFather dan olingan bot tokeningizni kiriting."
        )
        return

    logger.info("Bot ishga tushirilmoqda...")

    # Render Web Service uchun port serverini boshlash (agar PORT mavjud bo'lsa)
    health_runner = await start_dummy_health_server()

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
        if health_runner:
            await health_runner.cleanup()
        await bot.session.close()
        logger.info("Bot to'xtatildi va sessiya yopildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot foydalanuvchi tomonidan to'xtatildi.")
