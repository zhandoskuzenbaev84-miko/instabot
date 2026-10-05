# Universal Video & Media Downloader Telegram Bot

Ushbu bot har qanday platformadan (**Instagram, TikTok, YouTube & Shorts, Pinterest, Twitter/X, Facebook** va boshqalar) videolarni eng yuqori sifatda yuklab oladi. 
Videoning orqasida rasm bo'lsa ham yoki foto-slayd bo'lsa ham videoni to'liq taqdim etadi, shuningdek post tavsifi (opisaniya) va fon musiqasi nomini **alohida va bir bosishda nusxalanadigan (click-to-copy)** qilib yuboradi.

## 🚀 Asosiy Imkoniyatlar

- 📹 **Barcha platformalarni qo'llab-quvvatlash**: 
  - Instagram (Reels, Post, Karusel, Stories)
  - TikTok (Video, Foto slaydlar)
  - YouTube (Oddiy videolar va YouTube Shorts)
  - Pinterest (Video va Pinlar)
  - Twitter / X
  - Facebook (Reels va Watch)
  - Va boshqa 1000+ video manbalari
- 🎬 **Video ustuvorligi va kafolati**:
  - Videoning orqasida rasm bo'lsa ham yoki birinchi slayd rasm bo'lsa ham, videoni to'liq topib yuboradi.
  - Foto-slaydli postlar uchun (TikTok/Instagram audio bilan fotolar) avtomatik slaydshou video yaratib beradi.
  - Karusel postlarda videolarni alohida yo'qotmasdan taqdim etadi.
- 📝 **Alohida va oson nusxalanadigan Tavsif (Opisaniya)**:
  - Tavsif media ostida qisqartirilmaydi, balki **alohida xabar** sifatida yuboriladi.
  - `<code>` blokida joylashgani uchun foydalanuvchi matn ustiga bitta bosishi bilan butun opisaniyani nusxalab oladi (SMM va qayta yuklash uchun qulay).
  - Telegram 7.3+ mijozlarida "📋 Nusxa olish" tugmasi mavjud.
- 🎵 **Alohida musiqa nomi (Shazam integratsiyasi)**:
  - Fon musiqasi nomi alohida xabar sifatida chiqadi va ustiga bir bosishda nusxalanadi.
  - Agar postda musiqa nomi "Original sound" bo'lsa, videoning audiosi kesib olinib, **Shazam** orqali haqiqiy qo'shiq nomi va ijrochisi aniqlanadi.
- 🧹 **Xotirani avtomatik tozalash (Cleanup)**: Foydalanuvchiga media yuborilgach, yuklangan vaqtinchalik fayllar darhol xotiradan o'chiriladi.
- ⚡ **Asinxron va barqaror**: `aiogram 3.x`, `yt-dlp` va `ffmpeg` orqali tezkor va ishonchli ishlaydi.

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
│   └── downloader.py         # Linklarni qayta ishlash va mediani yuborish
├── services/
│   ├── __init__.py
│   ├── extractor.py          # yt-dlp va FFmpeg orqali media/video olish
│   └── music_recognition.py  # FFmpeg + Shazamio orqali musiqani aniqlash
└── utils/
    ├── __init__.py
    └── helpers.py            # Universal URL qidiruv, tozalash va formatlash
```

---

## 🛠 O'rnatish va Ishga Tushirish

### 1. Talablar
- **Python 3.10+**
- **FFmpeg**: Serverda/tizimda `ffmpeg` o'rnatilgan bo'lishi lozim (audiolarni kesish va videolarni qayta ishlash uchun).

### 2. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. Sozlamalar (.env)
`.env` faylini to'ldiring:
```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567
TEMP_DIR=downloads
MAX_FILE_SIZE_MB=50
```

### 4. Botni ishga tushirish
```bash
python main.py
```
