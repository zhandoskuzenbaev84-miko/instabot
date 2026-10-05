import html
import logging
from pathlib import Path
from typing import List, Union

from aiogram import Router, F
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramAPIError
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo, Message

from config import settings
from services.extractor import media_extractor
from utils.helpers import extract_platform_urls, format_response_caption

logger = logging.getLogger(__name__)

downloader_router = Router(name="downloader_router")


@downloader_router.message(F.text)
async def handle_media_download(message: Message):
    """
    Foydalanuvchi yuborgan xabardagi Instagram va TikTok havolalarini qayta ishlaydi.
    """
    text = message.text or ""
    urls = extract_platform_urls(text)
    
    if not urls:
        # Agar xabarda Instagram yoki TikTok linki bo'lmasa, e'tibor bermaymiz
        return

    # Faqat birinchi topilgan havolani olamiz
    url = urls[0]

    # Foydalanuvchiga jarayon boshlanganini bildirish
    status_msg = await message.reply("⏳ <b>Yuklanmoqda... Iltimos, kuting...</b>", parse_mode="HTML")
    
    # Telegramga "video yuklanmoqda" harakatini ko'rsatish
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO)

    media_data = None
    try:
        # Mediani yuklab olish va metama'lumotlarni chiqarish
        media_data = await media_extractor.extract_and_download(url)

        if not media_data or not media_data.files:
            await status_msg.edit_text(
                "❌ <b>Mediani yuklab bo'lmadi.</b>\n"
                "Iltimos, havola to'g'riligini va post ommaviy (ochiq profil) ekanligini tekshiring.",
                parse_mode="HTML"
            )
            return

        # Natija tavsifi va musiqasini formatlash
        caption_text = format_response_caption(media_data.caption, media_data.music)
        # Telegram caption chegarasi (1024 belgi)
        if len(caption_text) > 1024:
            caption_text = caption_text[:1020] + "..."

        # Maksimal fayl hajmi tekshiruvi (masalan, 50MB)
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        oversized = [f for f in media_data.files if f.stat().st_size > max_bytes]
        if oversized:
            await status_msg.edit_text(
                f"⚠️ <b>Fayl hajmi juda katta!</b>\n"
                f"Telegram botlari orqali faqat {settings.MAX_FILE_SIZE_MB} MB gacha bo'lgan fayllarni yuborish mumkin.",
                parse_mode="HTML"
            )
            return

        # 1. Bitta video bo'lsa
        if media_data.media_type == "video":
            video_file = FSInputFile(media_data.files[0])
            await message.reply_video(
                video=video_file,
                caption=caption_text,
                parse_mode="HTML",
                supports_streaming=True
            )

        # 2. Bitta rasm bo'lsa
        elif media_data.media_type == "photo":
            photo_file = FSInputFile(media_data.files[0])
            await message.reply_photo(
                photo=photo_file,
                caption=caption_text,
                parse_mode="HTML"
            )

        # 3. Karusel (album) bo'lsa
        elif media_data.media_type == "album":
            # Telegram bitta media groupda maksimal 10 ta fayl qabul qiladi
            group_files = media_data.files[:10]
            media_group: List[Union[InputMediaPhoto, InputMediaVideo]] = []

            for index, file_path in enumerate(group_files):
                is_first = (index == 0)
                item_caption = caption_text if is_first else None
                ext = file_path.suffix.lower()

                if ext in [".mp4", ".mov", ".mkv", ".webm"]:
                    media_group.append(
                        InputMediaVideo(
                            media=FSInputFile(file_path),
                            caption=item_caption,
                            parse_mode="HTML"
                        )
                    )
                else:
                    media_group.append(
                        InputMediaPhoto(
                            media=FSInputFile(file_path),
                            caption=item_caption,
                            parse_mode="HTML"
                        )
                    )

            await message.reply_media_group(media=media_group)

        # Jarayon tugagach status xabarini o'chirish
        try:
            await status_msg.delete()
        except TelegramAPIError:
            pass

    except Exception as e:
        logger.error(f"Xabarni yuborishda xatolik yuz berdi: {e}", exc_info=True)
        try:
            await status_msg.edit_text(
                "⚠️ <b>Kutilmagan xatolik yuz berdi.</b>\n"
                "Iltimos, qaytadan urinib ko'ring yoki boshqa havola yuboring.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    finally:
        # Xotirani to'ldirmasligi uchun vaqtinchalik barcha fayllarni tozalash (Cleanup)
        if media_data:
            media_data.cleanup()
