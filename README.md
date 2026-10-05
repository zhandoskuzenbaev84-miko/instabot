# Instagram & TikTok Media Downloader Telegram Bot

Ushbu bot Instagram (Reels, Post, Karusel) va TikTok platformalaridan video va rasmlarni yuqori sifatda yuklab oladi, post tavsifi (caption) va fon musiqasini (Shazam orqali) aniqlab foydalanuvchiga yuboradi.

## 🚀 Asosiy Imkoniyatlar

- 📹 **Instagram yuklovchi**: Reels, postlar va ko'p rasmli/videoli karusellar (MediaGroup formatida).
- 📱 **TikTok yuklovchi**: TikTok videolari suv belgisiz (watermark-free) sifatda.
- 📝 **Tavsif (Caption)**: Postning asl matni chiroyli qisqartirilib va tozalangan holda uzatiladi.
- 🎵 **Musiqa aniqlash (Shazam)**: Agar postdagi musiqa "Original sound" bo'lsa yoki topilmasa, videoning dastlabki 15 soniyasidan audio ajratib olinib, Shazam orqali haqiqiy trek nomi va ijrochisi aniqlanadi.
- 🧹 **Xotirani avtomatik tozalash (Cleanup)**: Foydalanuvchiga media yuborilgach, yuklangan vaqtinchalik fayllar darhol xotiradan o'chiriladi.
- ⚡ **Asinxron va tezkor**: `aiogram 3.x` va `asyncio` orqali ko'p foydalanuvchilar bilan bir vaqtda ishlay oladi.

---

## 📁 Loyiha Tuzilishi

```text
├── config.py                 # Bot konfiguratsiyasi (.env dan o'qish)
├── main.py                   # Botni ishga tushiruvchi asosiy fayl
├── requirements.txt          # Kerakli Python kutubxonalari
├── .env.example              # Muhit o'zgaruvchilari namunasi
├── handlers/
│   ├── __init__.py
│   ├── start.py              # /start va /help komandalari
│   └── downloader.py         # Linklarni qabul qilish va javob qaytarish
├── services/
│   ├── __init__.py
│   ├── extractor.py          # yt-dlp orqali media va metama'lumotlarni olish
│   └── music_recognition.py  # FFmpeg + Shazamio orqali musiqani aniqlash
└── utils/
    ├── __init__.py
    └── helpers.py            # Regex tekshiruvlari, tozalash va formatlash
```

---

## 🛠 O'rnatish va Ishga Tushirish

### 1. Talablar
- **Python 3.10+**
- **FFmpeg**: Serverda/tizimda `ffmpeg` o'rnatilgan bo'lishi lozim (audiolarni kesish va videolarni qayta ishlash uchun).
  - *Windows:* `winget install Gyan.FFmpeg` yoki rasmiy saytdan yuklab PATH ga qo'shish.
  - *Linux (Ubuntu/Debian):* `sudo apt update && sudo apt install -y ffmpeg`

### 2. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. Sozlamalar (.env)
`.env.example` faylidan nusxa olib `.env` faylini yarating:
```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567
TEMP_DIR=downloads
MAX_FILE_SIZE_MB=50
```
- `BOT_TOKEN`: [@BotFather](https://t.me/BotFather) dan olingan bot tokeni.

### 4. Botni ishga tushirish
```bash
python main.py
```

---

## 📋 Foydalanish
Telegramda botingizga kiring va `/start` bosing. Shundan so'ng istalgan ommaviy Instagram yoki TikTok havolasini yuboring. Bot mediani yuklab, formatlangan holda taqdim etadi:

```text
📝 Tavsif: Tabiatning ajoyib go'zalligi...
🎵 Musiqa: Billie Eilish - BIRDS OF A FEATHER
```
