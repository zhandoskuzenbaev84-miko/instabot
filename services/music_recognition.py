import asyncio
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Shazamio mavjudligini xavfsiz tekshirish
try:
    from shazamio import Shazam
    HAS_SHAZAMIO = True
except ImportError:
    Shazam = None
    HAS_SHAZAMIO = False
    logger.warning("shazamio kutubxonasi o'rnatilmagan yoki import qilib bo'lmadi.")


class MusicRecognizer:
    """Videodan musiqa nomini aniqlash servisi (FFmpeg + Shazamio)."""

    def __init__(self):
        self._shazam = Shazam() if HAS_SHAZAMIO else None

    async def extract_audio_sample(self, video_path: Path, output_audio_path: Path, duration: int = 15) -> bool:
        """
        FFmpeg yordamida videoning dastlabki 10-15 soniyasidan audio kesib oladi.
        """
        try:
            cmd = [
                "ffmpeg",
                "-y",  # mavjud faylni qayta yozish
                "-ss", "00:00:00",
                "-t", str(duration),
                "-i", str(video_path),
                "-vn",  # video oqimini olib tashlash
                "-acodec", "libmp3lame",
                "-ar", "44100",
                "-ac", "2",
                str(output_audio_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
            return process.returncode == 0 and output_audio_path.exists() and output_audio_path.stat().st_size > 0
        except Exception as e:
            logger.error(f"FFmpeg orqali audio kesishda xatolik: {e}")
            return False

    async def recognize_music_from_video(self, video_path: Path) -> Optional[str]:
        """
        Videodan audioni ajratib olib Shazam orqali musiqani aniqlaydi.
        Qaytaradi: "Ijrochi - Qo'shiq nomi" yoki None.
        """
        if not HAS_SHAZAMIO or not self._shazam:
            logger.info("Shazamio mavjud emasligi sababli audio aniqlash o'tkazib yuborildi.")
            return None

        if not video_path.exists() or video_path.stat().st_size == 0:
            return None

        # Vaqtinchalik audio fayl yo'li
        sample_audio_path = video_path.with_name(f"sample_{video_path.stem}.mp3")

        try:
            # 1. 15 soniyalik audio kesib olish
            extracted = await self.extract_audio_sample(video_path, sample_audio_path, duration=15)
            if not extracted:
                return None

            # 2. Shazamio orqali trekni qidirish
            recognition = await self._shazam.recognize(str(sample_audio_path))
            if not recognition:
                return None

            track = recognition.get("track")
            if track:
                title = track.get("title")
                subtitle = track.get("subtitle")  # Ijrochi nomi
                
                if subtitle and title:
                    return f"{subtitle} - {title}"
                elif title:
                    return title

            return None
        except Exception as e:
            logger.warning(f"Musiqani aniqlashda (Shazamio) xatolik yuz berdi: {e}")
            return None
        finally:
            # Vaqtinchalik audio faylni tozalash
            try:
                if sample_audio_path.exists():
                    sample_audio_path.unlink()
            except Exception as e:
                logger.debug(f"Vaqtinchalik audio namunani o'chirishda xatolik: {e}")


music_recognizer = MusicRecognizer()
