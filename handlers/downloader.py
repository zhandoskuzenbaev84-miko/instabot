import logging
from typing import List, Optional, Union

from aiogram import Router, F
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from config import settings
from services.extractor import media_extractor
from utils.helpers import (
    clean_caption,
    extract_platform_urls,
    format_caption_message,
    format_music_message,
)

logger = logging.getLogger(__name__)

downloader_router = Router(name="downloader_router")


def get_copy_keyboard(text_to_copy: str) -> Optional[InlineKeyboardMarkup]:
    """
    Foydalanuvchi bir bosishda nusxa olishi uchun 'Nusxa olish' inline tugmasi.
    Aiogram versiyasida CopyTextButton mavjud bo'lsa tugma qaytaradi, aks holda None.
    """
    try:
        from aiogram.types import CopyTextButton
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 Nusxa olish",
                        copy_text=CopyTextButton(text=text_to_copy)
                    )
                ]
            ]
        )
    except Exception:
        return None


@downloader_router.message(F.text)
async def handle_media_download(message: Message):
    """
    Foydalanuvchi yuborgan har qanday video havolasini (Instagram, TikTok, YouTube,
    Pinterest, Twitter/X, Facebook va h.k.) qabul qilib, yuklab beradi.
    """
    text = message.text or ""
    urls = extract_platform_urls(text)

    # Agar havolalar topilmasa
    if not urls:
        # Shaxsiy chatda foydalanuvchiga qanday havola yuborish kerakligini ko'rsatamiz
        if message.chat.type == "private" and not text.startswith("/"):
            await message.reply(
                "ℹ️ <b>Iltimos, video havolasini (linkini) yuboring!</b>\n\n"
                "Bot quyidagi platformalardan videolarni yuklay oladi:\n"
                "• 📱 <b>Instagram</b> (Reels, Post, Karusel)\n"
                "• 🎵 <b>TikTok</b> (Video, Foto slayd)\n"
                "• 🔴 <b>YouTube & Shorts</b>\n"
                "• 📌 <b>Pinterest</b>\n"
                "• 🐦 <b>Twitter / X</b>\n"
                "• 🔵 <b>Facebook</b>\n"
                "• Va boshqa barcha video platformalar!",
                parse_mode="HTML"
            )
        return

    # Birinchi topilgan havolani olamiz
    url = urls[0]

    # Foydalanuvchiga jarayon boshlanganini bildirish
    status_msg = await message.reply("⏳ <b>Yuklanmoqda... Iltimos, kuting...</b>", parse_mode="HTML")

    # Telegramga "video yuklanmoqda" harakatini ko'rsatish
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO)

    media_data = None
    try:
        # Mediani yuklab olish va metama'lumotlarni tahlil qilish
        media_data = await media_extractor.extract_and_download(url)

        if not media_data or not media_data.files:
            await status_msg.edit_text(
                "❌ <b>Mediani yuklab bo'lmadi.</b>\n"
                "Iltimos, havola to'g'riligini va post ommaviy (ochiq) ekanligini tekshiring.",
                parse_mode="HTML"
            )
            return

        # Maksimal fayl hajmi tekshiruvi (50 MB Telegram bot limiti)
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        oversized = [f for f in media_data.files if f.stat().st_size > max_bytes]
        if oversized:
            await status_msg.edit_text(
                f"⚠️ <b>Fayl hajmi juda katta!</b>\n"
                f"Telegram botlari orqali faqat {settings.MAX_FILE_SIZE_MB} MB gacha bo'lgan fayllarni yuborish mumkin.",
                parse_mode="HTML"
            )
            return

        # ---------------------------------------------------------------------
        # 1. MEDIA YUBORISH (VIDEOLAR VA RASMLAR)
        # "videoni orqasida rasm bo'lsa ham videoni chiqarib bersin"
        # ---------------------------------------------------------------------
        if media_data.video_files:
            # Agar bitta video bo'lsa
            if len(media_data.video_files) == 1:
                video_file = FSInputFile(media_data.video_files[0])
                await message.reply_video(
                    video=video_file,
                    supports_streaming=True
                )
            else:
                # Bir nechta video bo'lsa
                try:
                    video_group = [
                        InputMediaVideo(media=FSInputFile(v), supports_streaming=True)
                        for v in media_data.video_files[:10]
                    ]
                    await message.reply_media_group(media=video_group)
                except Exception as vid_err:
                    logger.warning(f"Media group orqali videolarni yuborishda xatolik, alohida yuboriladi: {vid_err}")
                    for v in media_data.video_files:
                        await message.reply_video(video=FSInputFile(v), supports_streaming=True)

            # Agar videoning orqasida yoki yonida rasmlar ham bo'lsa
            if media_data.photo_files:
                try:
                    if len(media_data.photo_files) == 1:
                        await message.reply_photo(photo=FSInputFile(media_data.photo_files[0]))
                    else:
                        photo_group = [
                            InputMediaPhoto(media=FSInputFile(p))
                            for p in media_data.photo_files[:10]
                        ]
                        await message.reply_media_group(media=photo_group)
                except Exception as p_err:
                    logger.warning(f"Rasmlarni yuborishda xatolik: {p_err}")
                    for p in media_data.photo_files[:10]:
                        try:
                            await message.reply_photo(photo=FSInputFile(p))
                        except Exception:
                            pass

        elif media_data.photo_files:
            # Faqat rasmlar bo'lsa (slaydshou hosil bo'lmagan holatda)
            if len(media_data.photo_files) == 1:
                await message.reply_photo(photo=FSInputFile(media_data.photo_files[0]))
            else:
                try:
                    photo_group = [
                        InputMediaPhoto(media=FSInputFile(p))
                        for p in media_data.photo_files[:10]
                    ]
                    await message.reply_media_group(media=photo_group)
                except Exception as p_err:
                    logger.warning(f"Rasmlarni media groupda yuborishda xatolik: {p_err}")
                    for p in media_data.photo_files[:10]:
                        try:
                            await message.reply_photo(photo=FSInputFile(p))
                        except Exception:
                            pass

        # ---------------------------------------------------------------------
        # 2. TAVSIFNI (OPISANIYANI) ALOHIDA OSON COPY QILINADIGAN QILIB YUBORISH
        # "va vedeoni tegidagi apisanyani alohoida oson copy qiloladingan bolib chiqsin"
        # ---------------------------------------------------------------------
        cleaned_caption_text = clean_caption(media_data.caption)
        if cleaned_caption_text:
            caption_message_text = format_caption_message(cleaned_caption_text)
            copy_button_markup = get_copy_keyboard(cleaned_caption_text)
            try:
                await message.reply(
                    text=caption_message_text,
                    parse_mode="HTML",
                    reply_markup=copy_button_markup
                )
            except Exception as cap_err:
                logger.warning(f"Tavsifni tugma bilan yuborishda xatolik: {cap_err}")
                await message.reply(
                    text=caption_message_text,
                    parse_mode="HTML"
                )

        # ---------------------------------------------------------------------
        # 3. MUZIQA NOMINI ALOHIDA YUBORISH
        # "muziqa nomi ham alohida bolib chiqsin"
        # ---------------------------------------------------------------------
        if media_data.music and media_data.music.strip():
            music_name_clean = media_data.music.strip()
            music_message_text = format_music_message(music_name_clean)
            music_button_markup = get_copy_keyboard(music_name_clean)
            try:
                await message.reply(
                    text=music_message_text,
                    parse_mode="HTML",
                    reply_markup=music_button_markup
                )
            except Exception as m_err:
                logger.warning(f"Musiqa xabarini tugma bilan yuborishda xatolik: {m_err}")
                await message.reply(
                    text=music_message_text,
                    parse_mode="HTML"
                )

        # Yuklash yakunlangach "Yuklanmoqda..." xabarini o'chirish
        try:
            await status_msg.delete()
        except TelegramAPIError:
            pass

    except Exception as e:
        logger.error(f"Xabarni qayta ishlashda xatolik yuz berdi: {e}", exc_info=True)
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
