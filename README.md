# avia_bot

MVP-бот для мониторинга aviation-safety.net и публикации новых авиаинцидентов в Telegram.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполните TELEGRAM_BOT_TOKEN и DEEPSEEK_API_KEY
python -m app.main --test-telegram
python -m app.main --once
```

После успешного однократного прогона запустите постоянный режим:

```bash
python -m app.main
```

## Режимы запуска

- `python -m app.main --test-telegram` — отправить тестовое сообщение в канал и выйти.
- `python -m app.main --once` — один цикл проверки ASN и публикации.
- `python -m app.main` — бесконечный воркер с интервалом `POLL_INTERVAL_MINUTES`.
- `DRY_RUN=true` — обработка без отправки в Telegram (для безопасной проверки).

## Что уже реализовано

- Сбор последних записей ASN (базовый HTML-парсер).
- Нормализация и генерация `incident_id`.
- Дедупликация через SQLite.
- Рерайт через DeepSeek API (или fallback, если ключ не задан).
- Валидация структуры поста.
- Публикация в Telegram-канал.
- Автозагрузка переменных окружения из `.env`.

## Ограничения MVP

- Парсер ASN может потребовать адаптации под изменения верстки.
- Валидация текста пока эвристическая.
- Нет отдельного retry-воркера и расширенной метрики.
