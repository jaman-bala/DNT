# DNT - Django-Ninja Template

Современный шаблон Django-Ninja проекта с энтерпрайз-архитектурой (DI, Async, Clean Architecture) и поддержкой последних технологий.

## 🚀 Особенности

- **Python 3.14+**: Использование новейших возможностей языка и высокая производительность.
- **Django 5.2+** с **Django-Ninja 1.6+** для быстрой разработки асинхронных API.
- **Enterprise Архитектура**: 
    - Четкое разделение на слои (Controller → Service → Repository).
    - **Dependency Injection**: Использование DI контейнера для управления зависимостями.
    - **Async First**: Полная поддержка асинхронности в БД и I/O операциях.
- **JWT Аутентификация**: Полный цикл с access/refresh токенами и хранением в HTTP-only cookies.
- **Docker Стек**: PostgreSQL, Redis, MinIO, RabbitMQ.
- **Инструментарий**: 
    - **uv**: Современный менеджер пакетов и окружения.
    - **ruff**: Быстрый линтер и форматировщик.
    - **pytest**: Полноценное тестирование с покрытием.
- **UI**: Кастомизированная админка на базе **Django Unfold**.

## 📁 Структура проекта

```
src/
├── apps/
│   ├── common/              # Общие контроллеры и сервисы (Upload и др.)
│   └── user/                # Модуль управления пользователями
│       ├── controllers/     # API эндпоинты (v1/)
│       ├── services/        # Бизнес-логика (Async)
│       ├── models/          # Модели базы данных
│       ├── dto/             # Pydantic схемы (Запросы и Ответы)
│       ├── repository/      # Слой работы с БД
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
cd django-ninja-template
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

## 🧪 Тестирование и линтинг

```bash
# Запуск тестов
uv run pytest

# Проверка кода линтером
uv run ruff check .
```

## 📚 Архитектура и DI

Подробное описание архитектурных решений проекта доступно в файле [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---
**DNT - Построен для масштабируемых и производительных систем.**

