import os
import re
import logging
import tempfile

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import yt_dlp

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
# Render сам подставляет этот адрес в переменную окружения RENDER_EXTERNAL_URL
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 10000))

URL_PATTERN = re.compile(
    r"(https?://(?:www\.)?(?:instagram\.com|instagr\.am|facebook\.com|fb\.watch)/\S+)"
)

# Ограничение Telegram Bot API на загрузку файлов ботом
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Путь к файлу с куками (Netscape cookies.txt).
# Вариант 1: Secret File на Render -> Settings -> Secret Files
COOKIES_FILE = os.environ.get("COOKIES_FILE", "/etc/secrets/cookies.txt")
# Вариант 2 (надёжнее): куки, закодированные в base64, в обычной
# переменной окружения COOKIES_B64 -> Settings -> Environment Variables.
# Так исключается проблема с табуляциями, которые может "съедать"
# текстовое поле при вставке.
COOKIES_B64 = os.environ.get("COOKIES_B64")
if COOKIES_B64:
    import base64

    decoded_path = "/tmp/cookies_from_env.txt"
    with open(decoded_path, "wb") as f:
        f.write(base64.b64decode(COOKIES_B64))
    COOKIES_FILE = decoded_path


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text:
        return

    match = URL_PATTERN.search(message.text)
    if not match:
        return

    url = match.group(1)
    status_msg = await message.reply_text("Скачиваю видео…")

    with tempfile.TemporaryDirectory() as tmpdir:
        outtmpl = os.path.join(tmpdir, "%(id)s.%(ext)s")
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "mp4/best",
            "quiet": True,
            "noplaylist": True,
            "max_filesize": MAX_FILE_SIZE,
        }
        if os.path.exists(COOKIES_FILE):
            ydl_opts["cookiefile"] = COOKIES_FILE

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
        except Exception as e:
            logger.exception("Ошибка скачивания")
            await status_msg.edit_text(f"Не удалось скачать видео: {e}")
            return

        if not os.path.exists(filename):
            await status_msg.edit_text("Видео не найдено (возможно, приватный аккаунт).")
            return

        if os.path.getsize(filename) > MAX_FILE_SIZE:
            await status_msg.edit_text("Видео слишком большое для отправки ботом (>50 МБ).")
            return

        try:
            with open(filename, "rb") as f:
                await message.reply_video(video=f, caption=info.get("title") or "")
        except Exception as e:
            logger.exception("Ошибка отправки")
            await status_msg.edit_text(f"Не удалось отправить видео: {e}")
            return

    await status_msg.delete()


def main() -> None:
    import asyncio

    if os.path.exists(COOKIES_FILE):
        logger.info("Cookies file FOUND at %s (size: %d bytes)", COOKIES_FILE, os.path.getsize(COOKIES_FILE))
    else:
        logger.warning("Cookies file NOT FOUND at %s", COOKIES_FILE)

    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    if WEBHOOK_URL:
        # Режим для Render (или любого хостинга с публичным URL)
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
        )
    else:
        # Локальный запуск / отладка
        application.run_polling()


if __name__ == "__main__":
    main()
