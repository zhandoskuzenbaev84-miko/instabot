import html
import logging
import os
import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Turli platformalar uchun qoliplar
INSTAGRAM_REGEX = re.compile(
    r"https?:\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/(?:[a-zA-Z0-9_\.]+\/)?(?:p|reel|reels|tv|share)\/([a-zA-Z0-9_\-\/]+)",
    re.IGNORECASE
)

TIKTOK_REGEX = re.compile(
    r"https?:\/\/(?:[a-zA-Z0-9_-]+\.)?tiktok\.com\/(?:@[\w.-]+\/video\/\d+|[\w.-]+|\S+)",
    re.IGNORECASE
)

YOUTUBE_REGEX = re.compile(
    r"https?:\/\/(?:www\.)?(?:youtube\.com\/(?:watch\?v=|shorts\/|v\/|embed\/)|youtu\.be\/)[\w-]+",
    re.IGNORECASE
)

PINTEREST_REGEX = re.compile(
    r"https?:\/\/(?:[a-zA-Z0-9_-]+\.)?(?:pinterest\.[a-z.]+|pin\.it)\/\S+",
    re.IGNORECASE
)

TWITTER_REGEX = re.compile(
    r"https?:\/\/(?:www\.)?(?:twitter\.com|x\.com)\/\w+\/status\/\d+",
    re.IGNORECASE
)

FACEBOOK_REGEX = re.compile(
    r"https?:\/\/(?:www\.|m\.|fb\.)?(?:facebook\.com|fb\.watch|fb\.me)\/\S+",
    re.IGNORECASE
)

# Har qanday URL qidirish uchun umumiy regex
URL_REGEX = re.compile(r"https?:\/\/[^\s]+", re.IGNORECASE)


def extract_platform_urls(text: str) -> List[str]:
    """
    Matndan har qanday video/media havolalarini (Instagram, TikTok, YouTube,
    Pinterest, Twitter/X, Facebook va boshqalar) ajratib oladi.
    """
    if not text:
        return []

    found_urls = URL_REGEX.findall(text)
    valid_urls = []
    for url in found_urls:
        # Link oxiridagi keraksiz belgilarni tozalash (qavs, tinish belgilari)
        cleaned = url.rstrip(").,;:?!>\"'»«]")
        try:
            parsed = urlparse(cleaned)
            # Kamida to'g'ri domen va sxema (http/https) bo'lishini tekshirish
            if parsed.scheme in ("http", "https") and "." in parsed.netloc:
                valid_urls.append(cleaned)
        except Exception:
            continue

    return valid_urls


def is_instagram_url(url: str) -> bool:
    """Havola Instagram'ga tegishlimi yoki yo'qligini tekshiradi."""
    return bool(INSTAGRAM_REGEX.search(url)) or ("instagram.com" in url or "instagr.am" in url)


def is_tiktok_url(url: str) -> bool:
    """Havola TikTok'ga tegishlimi yoki yo'qligini tekshiradi."""
    return bool(TIKTOK_REGEX.search(url)) or ("tiktok.com" in url)


def is_youtube_url(url: str) -> bool:
    """Havola YouTube yoki YouTube Shorts'ga tegishlimi tekshiradi."""
    return bool(YOUTUBE_REGEX.search(url)) or ("youtube.com" in url or "youtu.be" in url)


def is_pinterest_url(url: str) -> bool:
    """Havola Pinterest'ga tegishlimi tekshiradi."""
    return bool(PINTEREST_REGEX.search(url)) or ("pinterest." in url or "pin.it" in url)


def is_twitter_url(url: str) -> bool:
    """Havola Twitter/X ga tegishlimi tekshiradi."""
    return bool(TWITTER_REGEX.search(url)) or ("twitter.com" in url or "x.com" in url)


def is_facebook_url(url: str) -> bool:
    """Havola Facebook'ga tegishlimi tekshiradi."""
    return bool(FACEBOOK_REGEX.search(url)) or ("facebook.com" in url or "fb.watch" in url)


def clean_caption(caption: Optional[str], max_length: int = 3800) -> str:
    """
    Tavsif (caption) matnini tozalaydi va Telegram xabari chegarasiga moslaydi.
    """
    if not caption:
        return ""

    text = caption.strip()
    if len(text) > max_length:
        text = text[:max_length].rstrip() + "..."

    return text


def format_caption_message(caption: str) -> str:
    """
    Tavsif (opisaniya) uchun alohida xabar matnini formatlaydi.
    <code> tegi orqali bitta bosishda oson nusxalanadi (click-to-copy).
    """
    safe_text = html.escape(caption.strip())
    return (
        "📝 <b>Tavsif</b> <i>(nusxalash uchun matn ustiga bosing 👇):</i>\n\n"
        f"<code>{safe_text}</code>"
    )


def format_music_message(music: str) -> str:
    """
    Musiqa nomi uchun alohida xabar matnini formatlaydi.
    <code> tegi orqali bitta bosishda oson nusxalanadi (click-to-copy).
    """
    safe_music = html.escape(music.strip())
    return (
        "🎵 <b>Musiqa nomi</b> <i>(nusxalash uchun matn ustiga bosing 👇):</i>\n\n"
        f"<code>{safe_music}</code>"
    )


def format_response_caption(caption: Optional[str], music: Optional[str]) -> str:
    """
    Media ostidagi ixcham sarlavha (agar bitta xabarda kerak bo'lsa).
    """
    parts = []
    cleaned_caption = clean_caption(caption, max_length=600)
    if cleaned_caption:
        safe_caption = html.escape(cleaned_caption)
        parts.append(f"📝 <b>Tavsif:</b> {safe_caption}")

    if music and music.strip():
        safe_music = html.escape(music.strip())
        parts.append(f"🎵 <b>Musiqa:</b> {safe_music}")

    if not parts:
        return "✨ <i>Yuklab olindi</i>"

    return "\n\n".join(parts)


def cleanup_files(*file_paths: Optional[str | Path]) -> None:
    """
    Yuklangan vaqtinchalik fayllarni xavfsiz o'chiradi.
    """
    for file_path in file_paths:
        if not file_path:
            continue
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.info(f"Vaqtinchalik fayl o'chirildi: {path}")
        except Exception as e:
            logger.warning(f"Faylni o'chirishda xatolik yuz berdi ({file_path}): {e}")
