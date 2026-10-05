import html
import logging
import os
import re
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Instagram va TikTok havolalari uchun regex qoliplari
INSTAGRAM_REGEX = re.compile(
    r"https?:\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/(?:[a-zA-Z0-9_\.]+\/)?(?:p|reel|reels|tv|share)\/([a-zA-Z0-9_\-\/]+)",
    re.IGNORECASE
)

TIKTOK_REGEX = re.compile(
    r"https?:\/\/(?:[a-zA-Z0-9_-]+\.)?tiktok\.com\/(?:@[\w.-]+\/video\/\d+|[\w.-]+|\S+)",
    re.IGNORECASE
)

# Umumiy link qidirish regexi
URL_REGEX = re.compile(r"https?:\/\/[^\s]+")


def extract_platform_urls(text: str) -> List[str]:
    """
    Matndan Instagram yoki TikTok havolalarini ajratib oladi.
    """
    if not text:
        return []
    
    found_urls = URL_REGEX.findall(text)
    valid_urls = []
    for url in found_urls:
        # Link oxiridagi keraksiz belgilarni tozalash (masalan, qavs, nuqta)
        cleaned = url.rstrip(").,;:?!>\"'")
        if is_instagram_url(cleaned) or is_tiktok_url(cleaned):
            valid_urls.append(cleaned)
    return valid_urls


def is_instagram_url(url: str) -> bool:
    """Havola Instagram'ga tegishlimi yoki yo'qligini tekshiradi."""
    return bool(INSTAGRAM_REGEX.search(url)) or ("instagram.com" in url or "instagr.am" in url)


def is_tiktok_url(url: str) -> bool:
    """Havola TikTok'ga tegishlimi yoki yo'qligini tekshiradi."""
    return bool(TIKTOK_REGEX.search(url)) or ("tiktok.com" in url)


def clean_caption(caption: Optional[str], max_length: int = 700) -> str:
    """
    Tavsif (caption) matnini tozalaydi va Telegram limiti uchun qisqartiradi.
    """
    if not caption:
        return ""
    
    # Ortiqcha bo'shliqlar va yangi qatorlarni tartibga solish
    text = caption.strip()
    
    # Ko'p sonli ketma-ket hashtaglarni tozalash yoki qisqartirish
    # Agar matn max_length dan oshsa, xavfsiz qisqartirish
    if len(text) > max_length:
        text = text[:max_length].rstrip() + "..."
        
    return text


def format_response_caption(caption: Optional[str], music: Optional[str]) -> str:
    """
    Foydalanuvchiga yuboriladigan yakuniy xabar matnini formatlaydi:
    📝 Tavsif: ...
    🎵 Musiqa: ...
    """
    parts = []
    
    cleaned_caption = clean_caption(caption)
    if cleaned_caption:
        # Telegram HTML parse mode uchun xavfsiz qilish
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
