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
- **Rate limiting**: встроенная защита от брутфорса на `/auth/login`, `/auth/register`, `/auth/refresh` и `/common/upload`.
- **Фоновые задачи**: очередь на **arq** (Redis) для асинхронных джобов (email, обработка файлов и т.п.).
- **Docker Стек**: PostgreSQL, Redis, MinIO, arq worker.
- **CI/CD**: GitHub Actions (lint, тесты, bandit) + Dependabot для автоматического обновления зависимостей.
- **Инструментарий**: 
    - **uv**: Современный менеджер пакетов и окружения.
    - **ruff**: Быстрый линтер и форматировщик.
    - **pytest**: Полноценное тестирование с покрытием.
- **UI**: Кастомизированная админка на базе **Django Unfold**.

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

Документация Swagger доступна по адресу: http://localhost:8000/api/v1/docs

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

### Rate limiting

`/auth/login`, `/auth/register`, `/auth/refresh` и `/common/upload` защищены простым
async rate limiter'ом на Redis (`src/apps/common/utils/ratelimit.py`), без дополнительных
зависимостей. При превышении лимита эндпоинт возвращает `429`. Используйте
`enforce_rate_limit(...)` в своих новых эндпоинтах по тому же образцу.

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

