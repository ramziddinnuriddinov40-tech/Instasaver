# Telegram-бот: скачивание видео из Instagram / Facebook

Бот отслеживает в группе сообщения со ссылками на Instagram или Facebook,
скачивает видео (через `yt-dlp`) и отправляет его в ответ на сообщение
с ссылкой.

## 1. Создание бота

1. Напишите [@BotFather](https://t.me/BotFather), команда `/newbot`, получите `BOT_TOKEN`.
2. **Важно:** чтобы бот видел все сообщения в группе (а не только команды),
   отключите Privacy Mode: `/mybots` → выберите бота → `Bot Settings` →
   `Group Privacy` → `Turn off`.
3. Добавьте бота в нужную группу.

## 2. GitHub

1. Создайте новый репозиторий на GitHub.
2. Залейте туда файлы: `bot.py`, `requirements.txt`, `.gitignore`, `README.md`.

```bash
git init
git add .
git commit -m "Telegram video downloader bot"
git branch -M main
git remote add origin https://github.com/<ваш_логин>/<репозиторий>.git
git push -u origin main
```

## 3. Render (бесплатный тариф)

Бесплатный тариф Render даёт **Web Service**, а не отдельный воркер, поэтому
бот работает в режиме webhook и слушает порт, который Render передаёт в
переменной `PORT` — это уже реализовано в `bot.py`.

1. На [render.com](https://render.com) → **New** → **Web Service**.
2. Подключите созданный репозиторий.
3. Настройки:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
4. В разделе **Environment** добавьте переменную:
   - `BOT_TOKEN` = токен от BotFather
5. Задеплойте. Render автоматически даст переменную `RENDER_EXTERNAL_URL` —
   код сам использует её для установки вебхука, ничего дополнительно
   настраивать не нужно.

## Ограничения, о которых стоит знать

- Telegram-бот не может отправлять файлы **больше 50 МБ** — код это
  проверяет и сообщит об ошибке, если видео больше.
- Приватные аккаунты/посты Instagram и Facebook скачать не получится —
  `yt-dlp` не обходит авторизацию.
- Instagram и Facebook periodически меняют защиту от скачивания, из-за
  чего `yt-dlp` иногда может переставать скачивать — тогда нужно обновлять
  пакет (`yt-dlp>=...` в `requirements.txt`) до последней версии.
- Бесплатный тариф Render "засыпает" при неактивности и может медленно
  просыпаться — это ограничение тарифа, не кода.
