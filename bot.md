1. Tizim Arxitekturasi
Tizim modulli (modular) tuzilishi kerak, shunda Instagram yoki TikTok algoritmlari o‘zgarganda faqat ma'lum bitta servisni yangilash kifoya qiladi:

[ Telegram User ] 
       │ (Link yuboradi)
       ▼
[ Telegram Bot Gateway ] (aiogram 3.x)
       │
       ├──► Link validation & Platform router (Instagram / TikTok)
       │
       ├──► Downloader & Metadata Engine (yt-dlp / RapidAPI / Instaloader)
       │        ├── Media fayl (.mp4 / .jpg)
       │        ├── Tavsif (Caption / Description)
       │        └── Audio metadata (Track title & Artist)
       │
       ├──► (Ixtiyoriy) Audio Recognition Service (ShazamAPI / AudD)
       │        └── Agar platforma audioni "Original Audio" desa, musiqani aniqlash
       │
       └──► Response Dispatcher
                └── Foydalanuvchiga media + formatlangan matn (caption + musiqa) yuborish
2. Tavsiya etiladigan Texnologiyalar va Kutubxonalar
Bot Framework: aiogram 3.x (Python) — asinxron, tez va zamonaviy.

Media & Metadata yuklash:

yt-dlp: TikTok va Instagram Reels/Postlar uchun eng kuchli ochiq manbali vosita (video, audio, sarlavha, original audio nomini bir vaqtda oladi).

Alternativ (Production/Stabil): Instagram va TikTok anti-bot himoyasini aylanib o‘tish uchun bepul yt-dlp yetarli bo‘lmasa, RapidAPI (masalan, Instagram Scraper, TikTok All-in-One Downloader API) orqali integratsiya qilish tavsiya etiladi.

Musiqa aniqlash (Audio Recognition): shazamio (Python uchun Shazam API) — agar postda faqat "original sound" deb yozilgan bo‘lsa, audio trekni kesib olib haqiqiy musiqani topish uchun.

Vazifalar navbati (Task Queue): Celery + Redis yoki kichik loyiha bo‘lsa asyncio.create_task — bot video yuklanayotganda bloklanib qolmasligi uchun.

LLM (Matnni tahlil qilish yoki chiroyli formatlash uchun): google-genai (Gemini 2.5 Flash) yoki openai (GPT-4o-mini). Ular caption ichidagi keraksiz heshteglarni tozalash, matnni tarjima qilish yoki asosiy ma'noni ajratib berish uchun ishlatiladi.

3. CLI Agent / LLM uchun To‘liq PROMPT
Quyidagi promtni to‘g‘ridan-to‘g‘ri CLI vositangizga (Cursor, Aider, Claude Code va h.k.) nusxalab berishingiz mumkin:

Markdown
Sen professional Python backend muhandisisan. Menga Instagram va TikTok platformalaridan media yuklab beruvchi, ularning tavsifini (caption) va fon musiqasini aniqlab beruvchi to'liq Telegram bot kodini yozib ber.

### Loyiha Talablari:

1. **Texnologiyalar steki:**
   - Framework: `aiogram` (v3.x)
   - Media & Metadata extractor: `yt-dlp`
   - Musiqa qidiruv (Shazam): `shazamio` (agar metadatada musiqa nomi noma'lum bo'lsa)
   - Asinxron arxitektura (`asyncio`, `aiohttp`)
   - Konfiguratsiya: `pydantic-settings` yoki `python-dotenv`

2. **Funksional talablar:**
   - Foydalanuvchi Telegram botga Instagram (Reel, Post, Carousel) yoki TikTok linkini yuboradi.
   - Bot havolani taniydi va yuklash holati haqida xabar beradi ("Yuklanmoqda...").
   - `yt-dlp` yordamida:
     * Video yoki rasm(lar) yuklab olinadi.
     * Post matni (caption/description) olinadi.
     * Ovoz yo'li (audio track) nomi va ijrochisi olinadi.
   - Agar metadatada musiqa nomi topilmasa yoki "Original Sound" bo'lsa, videoning dastlabki 10-15 soniyasidagi audioni ajratib olib, `shazamio` orqali haqiqiy musiqa nomini aniqlasin.
   - Natija foydalanuvchiga yuboriladi:
     * Media: Video yoki Photo (karusel bo'lsa MediaGroup).
     * Matn formati:
       📝 **Tavsif:** {tozalangan caption}
       🎵 **Musiqa:** {ijrochi - musiqa nomi}
   - Yuklangan vaqtinchalik media fayllar xotirani to'ldirmasligi uchun yuborilgandan so'ng darhol o'chirib tashlanishi shart (cleanup).

3. **Loyiha tuzilishi (Clean Architecture):**
   ├── config.py (Bot tokeni va sozlamalar)
   ├── handlers/
   │   ├── start.py
   │   └── downloader.py (Linklarni qabul qilish va javob qaytarish)
   ├── services/
   │   ├── extractor.py (yt-dlp orqali media va metadata olish)
   │   └── music_recognition.py (Shazamio orqali musiqani aniqlash)
   ├── utils/
   │   └── helpers.py (Fayllarni tozalash, link regex tekshiruvlari)
   ├── main.py (Botni ishga tushirish)
   ├── requirements.txt
   └── .env.example

Barcha kerakli fayllarni, kodlarni, xatoliklarni ushlash (try-except) mexanizmlari va to'liq tushuntirish bilan birma-bir yozib ber.
4. O‘rnatilishi Kerak Bo‘lgan Kutubxonalar (requirements.txt)
Loyiha uchun kerak bo‘ladigan asosiy paketlar:

Plaintext
aiogram>=3.4.0
yt-dlp>=2024.03.10
shazamio>=0.5.1
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
aiofiles>=23.2.1
Tizim talabi: Videolarni qayta ishlash va audioni kesib olish uchun serverda ffmpeg o‘rnatilgan bo‘lishi shart (sudo apt install ffmpeg).