# avia_bot

MVP-бот для мониторинга aviation-safety.net и публикации новых авиаинцидентов в Telegram.

## Быстрый старт (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
# заполните TELEGRAM_BOT_TOKEN и DEEPSEEK_API_KEY
python3 -m app.main --test-telegram
python3 -m app.main --once
```

После успешного однократного прогона запустите постоянный режим:

```bash
python3 -m app.main
```

## Режимы запуска

- `python3 -m app.main --test-telegram` — отправить тестовое сообщение в канал и выйти.
- `python3 -m app.main --once` — один цикл проверки ASN и публикации (ошибки логируются, процесс завершается без бесконечного цикла).
- `python3 -m app.main` — бесконечный воркер с интервалом `POLL_INTERVAL_MINUTES`.
- `DRY_RUN=true` — обработка без отправки в Telegram (для безопасной проверки).

## Важные переменные в `.env`

- `ASN_FEED_URLS` — список URL через запятую; бот пройдет их по очереди, пока не получит валидный ответ.
  - По умолчанию: `https://aviation-safety.net/rss.xml,https://aviation-safety.net/asndb/year/<текущий_год>,https://aviation-safety.net/database/,https://aviation-safety.net/wikibase/dblist.php?Country=`

## Troubleshooting

### `zsh: command not found: python`
Используйте `python3` и `python3 -m pip` (на macOS часто нет алиаса `python`).

### `404 Not Found` на ASN
Источник ASN может менять URL/параметры. Обновите `ASN_FEED_URLS` в `.env` и перезапустите.
Например, рабочий URL со статьями за год: `https://aviation-safety.net/asndb/year/2026`.

### `Telegram sendMessage failed ... status=400`
Проверьте по шагам:

1. `TELEGRAM_CHANNEL` корректный (`@avia_crash` или числовой `-100...`).
2. Бот добавлен в канал как администратор с правом публикации.
3. Вы обращаетесь к правильному боту (токен из `@BotFather` для этого канала).

Теперь бот выводит детальную причину Telegram API в тексте ошибки (например `chat not found`).
Если Telegram вернул `can't parse entities`, бот автоматически делает повторную отправку без `parse_mode`.

### При запуске с `--test-telegram` всё равно стартует воркер
Вы запускаете старую версию кода. Обновите локальный проект (`git pull`) и убедитесь, что в `app/main.py` есть аргументы `--test-telegram` и `--once`.


### Перед повторным запуском после обновления

Если ранее проект падал на старом коде, выполните:

```bash
git pull
source .venv/bin/activate
python3 -m app.main --test-telegram
```

## Что уже реализовано

- Сбор последних записей ASN (RSS + табличный парсер + fallback по incident-ссылкам `/wikibase/` и `/database/record.php`).
- Нормализация и генерация `incident_id`.
- Дедупликация через SQLite.
- Рерайт через DeepSeek API (или fallback, если ключ не задан).
- Валидация структуры поста.
- Публикация в Telegram-канал.
- Автозагрузка переменных окружения из `.env`.
