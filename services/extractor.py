import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yt_dlp

from config import settings
from services.music_recognition import music_recognizer

logger = logging.getLogger(__name__)

GENERIC_AUDIO_NAMES = {
    "original sound",
    "original audio",
    "original",
    "asl ovoz",
    "asl audio",
    "оригинальный звук",
    "sound",
    "audio",
}


@dataclass
class ExtractedMedia:
    """Yuklab olingan media va uning metama'lumotlari."""
    task_id: str
    media_type: str  # "video", "photo", "album"
    files: List[Path] = field(default_factory=list)
    caption: str = ""
    music: Optional[str] = None
    source_url: str = ""

    def cleanup(self) -> None:
        """Yuklangan barcha fayllarni o'chiradi."""
        for file_path in self.files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"O'chirildi: {file_path}")
            except Exception as e:
                logger.warning(f"Faylni o'chirishda xatolik ({file_path}): {e}")


class MediaExtractor:
    """Instagram va TikTok uchun yt-dlp asosidagi yuklovchi va metama'lumotlar tahlilchisi."""

    def __init__(self, download_dir: Optional[Path] = None):
        self.download_dir = download_dir or settings.TEMP_DIR
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def _is_generic_sound(self, sound_name: Optional[str]) -> bool:
        """Ovoz nomi 'original sound' yoki umumiy nom ekanligini aniqlaydi."""
        if not sound_name:
            return True
        cleaned = sound_name.strip().lower()
        if cleaned in GENERIC_AUDIO_NAMES:
            return True
        for generic in GENERIC_AUDIO_NAMES:
            if cleaned.startswith(f"{generic} -") or cleaned.startswith(f"{generic} –"):
                return True
        return False

    def _sync_download(self, url: str, task_id: str) -> dict:
        """Sinxron yt-dlp yuklash funksiyasi (thread ichida ishga tushiriladi)."""
        output_template = str(self.download_dir / f"{task_id}_%(autonumber)02d_%(id)s.%(ext)s")
        
        ydl_opts = {
            "outtmpl": output_template,
            "format": "bestvideo*+bestaudio/best",
            "merge_output_format": "mp4",
            "noplaylist": False,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            # Instagram va TikTok uchun HTTP headerlari
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.sanitize_info(info) or {}

    async def extract_and_download(self, url: str) -> Optional[ExtractedMedia]:
        """
        Berilgan URL bo'yicha media va metama'lumotlarni asinxron yuklab oladi.
        """
        task_id = uuid.uuid4().hex[:10]
        
        try:
            # 1. Asinxron holda yt-dlp orqali yuklash
            info = await asyncio.to_thread(self._sync_download, url, task_id)
            if not info:
                logger.error(f"yt-dlp ma'lumot topa olmadi: {url}")
                return None

            # 2. Ushbu task_id ga tegishli yuklangan fayllarni topish
            downloaded_files = sorted(
                list(self.download_dir.glob(f"{task_id}_*")),
                key=lambda p: p.name
            )

            # Agar hech qanday fayl saqlanmagan bo'lsa
            if not downloaded_files:
                logger.error(f"Fayllar yuklanmadi: {url}")
                return None

            # 3. Metama'lumotlarni yig'ish (caption / tavsif)
            caption = (
                info.get("description")
                or info.get("title")
                or ""
            )

            # Agar playlist/karusel bo'lsa va umumiy description bo'sh bo'lsa
            if not caption and "entries" in info and info["entries"]:
                first_entry = info["entries"][0]
                if first_entry:
                    caption = first_entry.get("description") or first_entry.get("title") or ""

            # 4. Musiqa / Audio metama'lumotlarini aniqlash
            track = info.get("track")
            artist = info.get("artist")
            music_name: Optional[str] = None

            if track and artist:
                music_name = f"{artist} - {track}"
            elif track:
                music_name = track
            elif artist:
                music_name = artist

            # 5. Agar musiqa nomi yo'q bo'lsa yoki "Original sound" bo'lsa -> Shazamio orqali qidiramiz
            is_generic = self._is_generic_sound(music_name)
            
            # Videoni topish (musiqani aniqlash uchun)
            video_files = [
                f for f in downloaded_files
                if f.suffix.lower() in [".mp4", ".mov", ".mkv", ".webm"]
            ]
            photo_files = [
                f for f in downloaded_files
                if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
            ]

            if (is_generic or not music_name) and video_files:
                logger.info(f"Musiqa aniqlanmagan yoki original sound ({music_name}). Shazam orqali qidirilmoqda...")
                recognized = await music_recognizer.recognize_music_from_video(video_files[0])
                if recognized:
                    music_name = recognized
                    logger.info(f"Shazam musiqani aniqladi: {music_name}")
                elif not music_name and is_generic:
                    music_name = None  # Original sound deb xunuk ko'rsatmaslik

            # 6. Media turini belgilash
            if len(downloaded_files) > 1:
                media_type = "album"
            elif video_files:
                media_type = "video"
            elif photo_files:
                media_type = "photo"
            else:
                media_type = "video"

            return ExtractedMedia(
                task_id=task_id,
                media_type=media_type,
                files=downloaded_files,
                caption=caption,
                music=music_name,
                source_url=url,
            )

        except Exception as e:
            logger.error(f"Media yuklashda kutilmagan xatolik ({url}): {e}", exc_info=True)
            # Xatolik yuz berganda qolgan chala fayllarni tozalash
            for f in self.download_dir.glob(f"{task_id}_*"):
                try:
                    f.unlink()
                except Exception:
                    pass
            return None


media_extractor = MediaExtractor()
