# DNT - Django-Ninja Template

Современный шаблон Django-Ninja проекта с энтерпрайз-архитектурой (DI, Async, Clean Architecture) и поддержкой последних технологий.

## 🚀 Особенности

- **Python 3.14+**: Использование новейших возможностей языка и высокая производительность.
- **Django 6.0** с **Django-Ninja 1.6+** для быстрой разработки асинхронных API.
- **Enterprise Архитектура**: 
    - Четкое разделение на слои (Controller → Service → Model).
    - **Dependency Injection**: Использование DI контейнера для управления зависимостями.
    - **Async First**: Полная поддержка асинхронности в БД и I/O операциях.
- **JWT Аутентификация**: access/refresh токены через `Authorization: Bearer`, с blacklist отозванных токенов в Redis.
- **Password reset / Email verification**: одноразовые JWT-токены (`token_type` + blacklist), письма уходят через фоновую очередь.
- **Rate limiting**: встроенная защита от брутфорса на `/auth/login`, `/auth/register`, `/auth/refresh` и `/common/upload`.
- **Фоновые задачи**: очередь на **arq** (Redis) для асинхронных джобов (email, обработка файлов и т.п.).
- **Docker Стек**: PostgreSQL, Redis, MinIO, arq worker.
- **CI/CD**: GitHub Actions (lint, тесты, bandit) + Dependabot для автоматического обновления зависимостей.
- **Инструментарий**: 
    - **uv**: Современный менеджер пакетов и окружения.
    - **ruff**: Быстрый линтер и форматировщик.
    - **pytest**: Полноценное тестирование с покрытием.
- **UI**: Кастомизированная админка на базе **Django Unfold**.
- **Django Control Room** (dev-only): панели интроспекции URL-ов и Redis в админке + опциональный MCP-эндпоинт для AI-агентов.

## 📁 Структура проекта

```
src/
├── apps/
│   ├── common/              # Общие контроллеры и сервисы
│   │   ├── controllers/     # Upload и др. (v1/)
│   │   ├── services/        # S3Service, QueueService
│   │   ├── utils/           # ratelimit.py — переиспользуемый rate limiter
│   │   ├── worker.py        # Точка входа arq-воркера + фоновые задачи
│   │   └── tests/           # Тесты модуля
│   ├── note/                # Пример второго домена (см. "Добавление своего домена" ниже)
│   └── user/                # Модуль управления пользователями
│       ├── controllers/     # API эндпоинты (v1/)
│       ├── services/        # Бизнес-логика (Async)
│       ├── models/          # Модели базы данных (сервисы работают с Django ORM напрямую)
│       ├── dto/             # Pydantic схемы (Запросы и Ответы)
│       └── tests/           # Тесты модуля
├── config/
│   ├── base/                # Базовые классы для моделей и сервисов
│   ├── auth/                # Настройки аутентификации
│   ├── container.py         # DI Контейнер
│   ├── api.py               # Конфигурация NinjaAPI
│   └── settings.py          # Настройки проекта
└── manage.py
```

## 🛠 Установка и запуск

### Локальная разработка (с `uv`)

1. **Клонируйте репозиторий**
```bash
git clone <repository-url>
cd DNT
```

2. **Настройте окружение**
```bash
cp env.example .env
# Отредактируйте .env файл (БД, Redis и др.)
```

3. **Установите зависимости и запустите проект**
```bash
# Синхронизация зависимостей
uv sync

# Запуск миграций
uv run python src/manage.py migrate

# Создание суперпользователя
uv run python src/manage.py createsuperuser

# Запуск сервера разработки
uv run python src/manage.py runserver
```

### Docker (рекомендуется)

```bash
# Сборка и запуск всех сервисов
cd infra/docker
docker compose up --build -d

# Миграции внутри Docker
docker compose exec app python src/manage.py migrate
```

## 🔧 API Эндпоинты

Интерактивная документация (Scalar) доступна по адресу: http://localhost:8000/api/v1/docs
(рендерится через `config/openapi.py::Scalar` вместо стандартного Swagger UI из django-ninja).

### Примеры запросов

**Регистрация пользователя**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+996500500500",
    "password": "StrongPassword123!",
    "first_name": "Тестовое",
    "last_name": "Имя"
  }'
```

**Авторизация (Login)**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+996500500500",
    "password": "StrongPassword123!"
  }'
```

**Обновление токена**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

**Загрузка файла** (требует авторизации)
```bash
curl -X POST "http://localhost:8000/api/v1/common/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@photo.jpg" \
  -F "folder=avatars"
```
Допустимые расширения — `ALLOWED_UPLOAD_EXTENSIONS` (по умолчанию `jpg,jpeg,png,webp`), максимальный
размер файла — `MAX_UPLOAD_SIZE` (по умолчанию 10 МБ). Расширьте оба списка в
`src/config/conf/uploads.py` / `.env`, если вашим моделям нужны другие типы файлов —
не забудьте также дополнить `EXTENSION_CONTENT_TYPES` в
`src/apps/common/controllers/v1/upload.py`, иначе Content-Type не пройдёт проверку.

**Сброс пароля**
```bash
# 1. Запросить письмо со ссылкой (ответ одинаков независимо от того, найден ли email —
#    так нельзя проверить, зарегистрирован ли конкретный email в системе)
curl -X POST "http://localhost:8000/api/v1/auth/password-reset/request" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# 2. В dev-режиме письмо с токеном печатается в логи (`docker compose logs app worker`,
#    console email backend). Забрать оттуда токен и подтвердить новый пароль:
curl -X POST "http://localhost:8000/api/v1/auth/password-reset/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "TOKEN_FROM_EMAIL",
    "new_password": "NewStrongPassword123!",
    "confirm_password": "NewStrongPassword123!"
  }'
```
Токен живёт 30 минут и одноразовый (после использования попадает в тот же Redis-blacklist,
что и токены logout).

**Подтверждение email**
```bash
# Письмо со ссылкой уходит автоматически при регистрации (если указан email).
# Повторно запросить его может только авторизованный пользователь:
curl -X POST "http://localhost:8000/api/v1/auth/email/verify/resend" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

curl -X POST "http://localhost:8000/api/v1/auth/email/verify/confirm" \
  -H "Content-Type: application/json" \
  -d '{"token": "TOKEN_FROM_EMAIL"}'
```
Подтверждение email **не блокирует** вход по умолчанию. Чтобы это включить (например,
в проде), поставьте `REQUIRE_EMAIL_VERIFICATION=True` в `.env` — тогда `login` будет
возвращать `403`, пока пользователь с указанным email его не подтвердит.
Настройки почты — `EMAIL_*` / `DEFAULT_FROM_EMAIL` / `FRONTEND_URL` в `env.example`;
по умолчанию используется console backend (письма печатаются в лог), для реальной
отправки укажите `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` и SMTP-креды.

### Rate limiting

`/auth/login`, `/auth/register`, `/auth/refresh`, `/common/upload` и все эндпоинты
password-reset/email-verify защищены простым async rate limiter'ом на Redis
(`src/apps/common/utils/ratelimit.py`), без дополнительных зависимостей. При превышении
лимита эндпоинт возвращает `429`. Используйте `enforce_rate_limit(...)` в своих новых
эндпоинтах по тому же образцу.

## 🕒 Фоновые задачи (arq)

Очередь на **arq** использует тот же Redis, что и кеш. Воркер поднимается отдельным
сервисом в `docker-compose.yml`:

```bash
docker compose exec worker arq apps.common.worker.WorkerSettings
# или, если контейнер не запущен:
docker compose logs -f worker
```

Чтобы добавить свою задачу:
1. Опишите `async def` функцию в `src/apps/common/worker.py` и добавьте её в
   `WorkerSettings.functions`.
2. Ставьте её в очередь из любого места через
   `await container.queue_service.enqueue("job_name", *args, **kwargs)`.

Пример (`log_event`) уже вызывается при регистрации пользователя — используйте его как
шаблон для реальных задач (письма, обработка загруженных файлов и т.п.).

## 🧩 Добавление своего домена

Всё, что связано с `apps/user`, специфично для auth (JWT, хеширование пароля, уникальный
телефон) — не лучший образец для копирования под свою модель. Вместо этого используйте
`apps/note` — минимальный CRUD-ресурс "заметка, принадлежащая пользователю", который
показывает тот же паттерн Controller → Service → Model без auth-специфики:

```bash
curl -X POST "http://localhost:8000/api/v1/notes/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Shopping list", "content": "Milk, eggs, bread"}'

curl "http://localhost:8000/api/v1/notes/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Чтобы добавить свой домен — скопируйте структуру `src/apps/note/` (`models/`, `dto/`,
`services/`, `controllers/v1/`, `exceptions.py`, `admin.py`, `tests/`) и переименуйте:

1. Модель наследуется от `BaseModel` (`config/base/base_model.py`) — UUID/timestamps/
   soft-delete уже включены.
2. Сервис — обычный класс с async-методами, каждый метод сам проверяет владельца
   (`owner=user` в фильтре), а не полагается на 403 — так по чужому `note_id` нельзя
   узнать, существует ли он вообще (тот же принцип, что и в password-reset).
3. Зарегистрируйте сервис в `config/container.py`, роутер и обработчики исключений —
   в `config/api.py`, приложение — в `config/conf/installed_apps.py::MY_APPS`.
4. `uv run python src/manage.py makemigrations <your_app>`.

## 🕹 Django Control Room (только для DEBUG)

[dj-urls-panel](https://django-control-room.github.io/dj-urls-panel/) даёт интроспекцию
всех URL проекта прямо из админки: поиск по паттерну/имени/вьюхе, детали каждого урла,
автоопределение DRF-сериализаторов. [dj-redis-panel](https://django-control-room.github.io/dj-redis-panel/)
даёт то же самое для Redis — просмотр ключей всех типов (string/list/set/hash/sorted set),
TTL, память, поиск по паттерну — уже настроен на тот же Redis, что использует кэш/rate
limiting/arq (`config/conf/control_room.py::DJ_REDIS_PANEL_SETTINGS`). Оба подключены так
же, как `django-debug-toolbar` — пакеты и приложения активны только при `DEBUG=True`, в
проде их просто нет.

Открой (залогинившись как staff-пользователь):

```
http://localhost:8000/admin/dj-urls-panel/    # список и детали URL
http://localhost:8000/admin/dj-redis-panel/   # ключи Redis
http://localhost:8000/admin/dj-control-room/  # общий дашборд
```

По умолчанию `ALLOW_KEY_DELETE=False` для Redis-панели — редактировать/смотреть TTL можно,
удалять ключи из общего dev-инстанса — нет (поменяйте в `DJ_REDIS_PANEL_SETTINGS`, если нужно).

Тема подстроена под Django Unfold (`config/conf/control_room.py`).

### AI-агенты (MCP)

`dj-control-room` умеет отдавать `list_urls`, `get_url_detail`, `inspect_view` AI-агентам
(Cursor, Claude и т.п.) через единый MCP-эндпоинт `/admin/dj-control-room/mcp/`. Выключен
по умолчанию — включается тремя переменными в `.env`:

```bash
DJ_CONTROL_ROOM_MCP_ENABLED=True
DJ_CONTROL_ROOM_MCP_TOKEN=change-me-to-a-long-random-secret
DJ_CONTROL_ROOM_MCP_USERNAME=your-staff-username  # должен существовать и быть is_staff
```

Агент авторизуется `Authorization: Bearer <DJ_CONTROL_ROOM_MCP_TOKEN>`, а разрешения на
каждый вызов инструмента проверяются от имени `MCP_USERNAME`.

## 🧪 Тестирование и линтинг

```bash
# Запуск тестов
uv run pytest

# Проверка кода линтером
uv run ruff check .
uv run ruff format --check .

# Security-линтер
uv run bandit -r src -ll -ii
```

CI (`.github/workflows/ci.yml`) прогоняет всё это на каждый push/PR в `master`.

## 📦 Обновление зависимостей

Все зависимости в `pyproject.toml` закреплены с верхней границей (например
`django>=6.0.3,<7.0`), чтобы `uv sync`/`uv lock --upgrade` не мог молча перескочить на
следующий мажор. Dependabot (`.github/dependabot.yml`) еженедельно открывает PR на
обновления `uv`, GitHub Actions и Docker-образов — они проходят через тот же CI, что и
любой другой PR.

## 📚 Архитектура и DI

Подробное описание архитектурных решений проекта доступно в файле [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 📄 Лицензия

[MIT](LICENSE) — используйте, форкайте и адаптируйте свободно, в том числе в коммерческих проектах.

---
**DNT - Построен для масштабируемых и производительных систем.**

