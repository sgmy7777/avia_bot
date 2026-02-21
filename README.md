# avia_bot

MVP-бот для мониторинга aviation-safety.net и публикации новых авиаинцидентов в Telegram.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export $(cat .env | xargs)
python -m app.main
```

## Что уже реализовано

- Сбор последних записей ASN (базовый HTML-парсер).
- Нормализация и генерация `incident_id`.
- Дедупликация через SQLite.
- Рерайт через DeepSeek API (или fallback, если ключ не задан).
- Валидация структуры поста.
- Публикация в Telegram-канал.

## Ограничения MVP

- Парсер ASN может потребовать адаптации под изменения верстки.
- Валидация текста пока эвристическая.
- Нет отдельного retry-воркера и расширенной метрики.
