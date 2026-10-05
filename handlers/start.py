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
        "Men har qanday platformadan <b>video va rasmlarni</b> eng yuqori sifatda yuklab beruvchi universal botman!\n\n"
        "🚀 <b>Asosiy imkoniyatlar:</b>\n"
        "• 📹 <b>Barcha platformalar:</b> Instagram, TikTok, YouTube & Shorts, Pinterest, Twitter / X, Facebook va h.k.\n"
        "• 🎬 <b>Video kafolati:</b> Videoning orqasida rasm bo'lsa ham yoki foto-slayd bo'lsa ham videoni chiqarib beradi!\n"
        "• 📝 <b>Alohida tavsif (opisaniya):</b> Matn ustiga bir marta bosish orqali oson nusxalash (click-to-copy)\n"
        "• 🎵 <b>Alohida musiqa nomi:</b> Fon musiqasi nomi ham alohida nusxalanadigan bo'lib chiqadi\n\n"
        "📥 <b>Ishlatish:</b> Shunchaki xohlagan video havolasini (linkini) yuboring!"
    )
    await message.answer(text, parse_mode="HTML")


@start_router.message(Command("help"))
async def handle_help(message: Message):
    """/help komandasi uchun handler."""
    text = (
        "ℹ️ <b>Qanday foydalanish kerak?</b>\n\n"
        "1. Xohlagan ilovadan (Instagram, TikTok, YouTube, Pinterest va boshqalar) kerakli video havolasini nusxalang.\n"
        "2. Havolani ushbu botga yuboring.\n"
        "3. Bot bir necha soniya ichida:\n"
        "   — Videoni to'liq sifatda yuboradi\n"
        "   — Opisaniyani (tavsif) alohida nusxalashga qulay qilib taqdim etadi\n"
        "   — Musiqa nomini alohida taqdim etadi.\n\n"
        "⚠️ <i>Eslatma: Shaxsiy (private/yopiq) profillardagi videolarni yuklab bo'lmaydi.</i>"
    )
    await message.answer(text, parse_mode="HTML")
