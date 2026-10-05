#!/usr/bin/env bash
# Render Native Python build script
set -o errexit

# Python paketlarini o'rnatish
pip install -r requirements.txt

# Render Native Linux muhitida FFmpeg yo'q bo'lsa, statik binarini yuklab olamiz
if ! command -v ffmpeg &> /dev/null; then
    echo "FFmpeg mavjud emas. Render uchun statik FFmpeg yuklanmoqda..."
    mkdir -p "$PWD/bin"
    curl -sL https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz | tar -xJ --strip-components=2 -C "$PWD/bin" */bin/ffmpeg */bin/ffprobe || true
    chmod +x "$PWD/bin/ffmpeg" "$PWD/bin/ffprobe" || true
    export PATH="$PWD/bin:$PATH"
    echo "FFmpeg muvaffaqiyatli yuklandi!"
fi
