from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

start_router = Router(name="start_router")


@start_router.message(CommandStart())
async def handle_start(message: Message):
    """/start komandasi uchun handler."""
    user_name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
    text = (
        f"👋 <b>Assalomu alaykum, {user_name}!</b>\n\n"
        "Men <b>Instagram</b> va <b>TikTok</b> platformalaridan video va rasmlarni yuklab beruvchi botman.\n\n"
        "🚀 <b>Asosiy imkoniyatlar:</b>\n"
        "• 📹 Instagram Reels, Post va Karusellar\n"
        "• 📱 TikTok videolari\n"
        "• 📝 Post tavsifi (caption)\n"
        "• 🎵 Videodagi fon musiqasini aniqlash (Shazam)\n\n"
        "📥 <b>Ishlatish juda oddiy:</b>\n"
        "Menga shunchaki Instagram yoki TikTok havolasini yuboring!"
    )
    await message.answer(text, parse_mode="HTML")


@start_router.message(Command("help"))
async def handle_help(message: Message):
    """/help komandasi uchun handler."""
    text = (
        "ℹ️ <b>Qanday foydalanish kerak?</b>\n\n"
        "1. Instagram yoki TikTok ilovasidan kerakli post havolasini nusxalang (Share ➡️ Copy link).\n"
        "2. Havolani ushbu botga xabar sifatida yuboring.\n"
        "3. Bot bir necha soniya ichida videoni/rasmni uning tavsifi va musiqasi bilan sizga taqdim etadi.\n\n"
        "⚠️ <i>Eslatma: Shaxsiy (private) akkauntlardagi videolarni yuklab bo'lmaydi.</i>"
    )
    await message.answer(text, parse_mode="HTML")
