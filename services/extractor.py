import asyncio
import logging
import shutil
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
    "оригинальное аудио",
    "sound",
    "audio",
}


@dataclass
class ExtractedMedia:
    """Yuklab olingan media va uning metama'lumotlari."""
    task_id: str
    media_type: str  # "video", "videos", "photo", "photos", "mixed"
    files: List[Path] = field(default_factory=list)
    video_files: List[Path] = field(default_factory=list)
    photo_files: List[Path] = field(default_factory=list)
    audio_files: List[Path] = field(default_factory=list)
    caption: str = ""
    music: Optional[str] = None
    source_url: str = ""

    def cleanup(self) -> None:
        """Yuklangan barcha vaqtinchalik fayllarni xavfsiz o'chiradi."""
        # files ro'yxatidagi barcha fayllar va task_id bilan bog'liq har qanday qoldiq fayllar
        all_to_clean = set(self.files + self.video_files + self.photo_files + self.audio_files)
        for file_path in all_to_clean:
            try:
                if file_path and file_path.exists():
                    file_path.unlink()
                    logger.info(f"O'chirildi: {file_path}")
            except Exception as e:
                logger.warning(f"Faylni o'chirishda xatolik ({file_path}): {e}")


class MediaExtractor:
    """Barcha platformalar uchun yt-dlp asosidagi universal media va metadata yuklovchi."""

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
            if cleaned.startswith(f"{generic} -") or cleaned.startswith(f"{generic} –") or cleaned.startswith(f"{generic}_"):
                return True
        return False

    def _sync_download(self, url: str, task_id: str) -> dict:
        """Sinxron yt-dlp yuklash funksiyasi (thread ichida ishga tushiriladi)."""
        output_template = str(self.download_dir / f"{task_id}_%(autonumber)02d_%(id)s.%(ext)s")

        ydl_opts = {
            "outtmpl": output_template,
            # Universal sifat: eng yaxshi mp4 video + m4a audio, yoki har qanday video+audio birlashtirish
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "noplaylist": False,  # Karusel postlardagi barcha slaydlarni olish
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.sanitize_info(info) or {}

    async def _create_slideshow_video(
        self,
        task_id: str,
        photo_files: List[Path],
        audio_file: Optional[Path]
    ) -> Optional[Path]:
        """
        Rasmlar va audiodan MP4 video (slaydshou) hosil qiladi.
        Bu TikTok/Instagram foto-slaydlari uchun 'videoni orqasida rasm bo'lsa ham'
        videoni taqdim etishga xizmat qiladi.
        """
        if not photo_files:
            return None

        ffmpeg_exe = shutil.which("ffmpeg") or "ffmpeg"
        output_video = self.download_dir / f"{task_id}_slideshow.mp4"
        list_file = self.download_dir / f"{task_id}_concat.txt"

        try:
            # Concat demuxer uchun ro'yxat tuzish (har bir rasm 3 soniyadan)
            lines = []
            for p in photo_files:
                resolved_str = str(p.resolve()).replace("\\", "/")
                lines.append(f"file '{resolved_str}'")
                lines.append("duration 3")

            # Concat demuxer qoidasiga ko'ra, oxirgi rasm yana bir bor ko'rsatiladi
            if photo_files:
                last_resolved = str(photo_files[-1].resolve()).replace("\\", "/")
                lines.append(f"file '{last_resolved}'")

            list_file.write_text("\n".join(lines), encoding="utf-8")

            cmd = [
                ffmpeg_exe,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file.resolve()),
            ]

            if audio_file and audio_file.exists():
                cmd.extend([
                    "-i", str(audio_file.resolve()),
                    "-c:a", "aac",
                    "-shortest"
                ])

            cmd.extend([
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "25",
                # Telegram uchun juft pikselli o'lchamga keltirish
                "-vf", "scale='if(gt(a,1),1080,-2)':'if(gt(a,1),-2,1080)':force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2",
                str(output_video.resolve())
            ])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()

            if output_video.exists() and output_video.stat().st_size > 0:
                logger.info(f"Slaydshou video tayyorlandi: {output_video}")
                return output_video

        except Exception as e:
            logger.warning(f"Slaydshou video yaratishda xatolik: {e}")
        finally:
            if list_file.exists():
                try:
                    list_file.unlink()
                except Exception:
                    pass

        return None

    async def extract_and_download(self, url: str) -> Optional[ExtractedMedia]:
        """
        Berilgan URL bo'yicha media va metama'lumotlarni asinxron yuklab oladi.
        """
        task_id = uuid.uuid4().hex[:10]

        try:
            # 1. Asinxron holda yt-dlp orqali yuklash
            info = await asyncio.to_thread(self._sync_download, url, task_id)
            if not info:
                logger.error(f"yt-dlp ma'lumot ololmadi: {url}")
                return None

            # 2. Yuklangan barcha fayllarni topish
            all_files = sorted(
                list(self.download_dir.glob(f"{task_id}_*")),
                key=lambda p: p.name
            )

            # Vaqtinchalik yoki yaroqsiz fayllarni chiqarib tashlash
            downloaded_files = [
                f for f in all_files
                if f.suffix.lower() not in [".txt", ".part", ".ytdl", ".temp"] and f.is_file()
            ]

            if not downloaded_files:
                logger.error(f"Hech qanday fayl yuklanmadi: {url}")
                return None

            # Fayllarni turlariga ajratish
            video_files = [
                f for f in downloaded_files
                if f.suffix.lower() in [".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"]
            ]
            photo_files = [
                f for f in downloaded_files
                if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".heic"]
            ]
            audio_files = [
                f for f in downloaded_files
                if f.suffix.lower() in [".mp3", ".m4a", ".aac", ".wav", ".ogg", ".opus"]
            ]

            # 3. Agar video bo'lmasa, lekin rasmlar bo'lsa (masalan TikTok foto slayd)
            # "videoning orqasida rasm bo'lsa ham videoni chiqarib bersin" talabi bo'yicha video yaratamiz
            if not video_files and photo_files:
                audio_ref = audio_files[0] if audio_files else None
                slideshow_vid = await self._create_slideshow_video(task_id, photo_files, audio_ref)
                if slideshow_vid:
                    video_files.append(slideshow_vid)
                    downloaded_files.append(slideshow_vid)

            # 4. Metama'lumotlarni yig'ish (Tavsif / Caption)
            caption = (
                info.get("description")
                or info.get("title")
                or ""
            ).strip()

            # Agar playlist/karusel bo'lsa va umumiy description bo'sh bo'lsa
            if not caption and "entries" in info and info["entries"]:
                for entry in info["entries"]:
                    if entry:
                        entry_c = entry.get("description") or entry.get("title")
                        if entry_c:
                            caption = entry_c.strip()
                            break

            # 5. Musiqa / Audio metama'lumotlarini aniqlash
            track = info.get("track")
            artist = info.get("artist")
            music_name: Optional[str] = None

            if track and artist:
                music_name = f"{artist} - {track}"
            elif track:
                music_name = track
            elif artist:
                music_name = artist

            if not music_name:
                music_name = info.get("music_title") or info.get("alt_title")

            if not music_name and "entries" in info and info["entries"]:
                for entry in info["entries"]:
                    if entry:
                        e_track = entry.get("track")
                        e_artist = entry.get("artist")
                        if e_track and e_artist:
                            music_name = f"{e_artist} - {e_track}"
                            break
                        elif e_track:
                            music_name = e_track
                            break
                        elif entry.get("music_title"):
                            music_name = entry.get("music_title")
                            break

            # 6. Musiqa nomi generic yoki topilmagan bo'lsa Shazam orqali tekshirish
            is_generic = self._is_generic_sound(music_name)

            media_for_shazam = video_files[0] if video_files else (audio_files[0] if audio_files else None)
            if (is_generic or not music_name) and media_for_shazam:
                logger.info(f"Musiqa aniqlanmagan yoki umumiy nom ({music_name}). Shazam orqali qidirilmoqda...")
                recognized = await music_recognizer.recognize_music_from_video(media_for_shazam)
                if recognized:
                    music_name = recognized
                    logger.info(f"Shazam musiqani aniqladi: {music_name}")
                elif is_generic:
                    music_name = None  # Foydalanuvchiga 'original sound' ko'rsatilmaydi

            # 7. Media turini belgilash
            if video_files and photo_files:
                media_type = "mixed"
            elif len(video_files) > 1:
                media_type = "videos"
            elif len(video_files) == 1:
                media_type = "video"
            elif len(photo_files) > 1:
                media_type = "photos"
            elif len(photo_files) == 1:
                media_type = "photo"
            else:
                media_type = "video"

            return ExtractedMedia(
                task_id=task_id,
                media_type=media_type,
                files=downloaded_files,
                video_files=video_files,
                photo_files=photo_files,
                audio_files=audio_files,
                caption=caption,
                music=music_name,
                source_url=url,
            )

        except Exception as e:
            logger.error(f"Media yuklashda kutilmagan xatolik ({url}): {e}", exc_info=True)
            # Xatolik yuz berganda barcha qoldiq fayllarni tozalash
            for f in self.download_dir.glob(f"{task_id}_*"):
                try:
                    f.unlink()
                except Exception:
                    pass
            return None


media_extractor = MediaExtractor()
