# Django-Ninja Template

Современный шаблон Django-Ninja проекта с лучшими практиками разработки.

## 🚀 Особенности

- **Django 5.2+** с Django-Ninja для быстрой разработки API
- **Современная архитектура** с разделением на слои (Controller → Service → Repository)
- **JWT аутентификация** с refresh токенами
- **Docker контейнеризация** с полным стеком (PostgreSQL, Redis, MinIO, RabbitMQ)
- **Pydantic схемы** для валидации данных
- **Comprehensive тестирование** с pytest
- **Code quality** с ruff, mypy, coverage
- **Безопасность** с CORS, CSRF защитой
- **Готовность к продакшену** с gunicorn, health checks

## 📁 Структура проекта

```
src/
├── apps/
│   └── user/
│       ├── controllers/     # API endpoints
│       ├── services/        # Business logic
│       ├── models/          # Database models
│       ├── dto/             # Pydantic schemas
│       └── tests/           # Unit tests
├── config/
│   ├── conf/                # Split settings
│   ├── auth/                # Authentication
│   └── settings.py          # Main settings
└── manage.py
```

## 🛠 Установка и запуск

### Локальная разработка

1. **Клонируйте репозиторий**
```bash
git clone <repository-url>
cd django-ninja-template
```

2. **Установите зависимости**
```bash
# Используем uv для быстрой установки
uv sync
```

3. **Настройте окружение**
```bash
cp env.example .env
# Отредактируйте .env файл под ваши нужды
```

4. **Запустите миграции**
```bash
uv run python src/manage.py migrate
```

5. **Создайте суперпользователя**
```bash
uv run python src/manage.py createsuperuser
```

6. **Запустите сервер**
```bash
uv run python src/manage.py runserver
```

### Docker (рекомендуется)

1. **Запустите все сервисы**
```bash
cd infra/docker
docker compose up --build
```

2. **Выполните миграции**
```bash
docker compose exec app python src/manage.py migrate
```

3. **Создайте суперпользователя**
```bash
docker compose exec app python src/manage.py createsuperuser
```

## 🔧 API Endpoints

После запуска сервера доступны следующие endpoints:

- **API Documentation**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:8000/admin
- **User API**: http://localhost:8000/api/v1/users/

### Примеры запросов

**Регистрация пользователя**
```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "fio": "Test User"
  }'
```

**Авторизация**
```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

**Получение профиля (требует токен)**
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
uv run pytest

# Запуск с покрытием
uv run pytest --cov=apps --cov-report=html

# Запуск конкретного теста
uv run pytest src/apps/user/tests/test_views.py::UserAPITestCase::test_user_registration
```

## 🔍 Code Quality

```bash
# Форматирование кода
uv run ruff format .

# Проверка стиля
uv run ruff check .

# Исправление автоисправимых ошибок
uv run ruff check . --fix
```

## 🐳 Docker сервисы

- **app**: Django приложение (порт 8000)
- **postgres**: PostgreSQL база данных (порт 5432)
- **redis**: Redis кеш (порт 6379)
- **minio**: S3-совместимое хранилище (порт 9000)
- **rabbitmq**: Message broker (порт 5672)

## 🔐 Безопасность

- JWT токены с refresh механизмом
- CORS настройки для фронтенда
- CSRF защита
- Валидация входных данных с Pydantic
- Безопасные настройки по умолчанию

## 📦 Зависимости

### Основные
- Django 5.2+
- Django-Ninja 1.4+
- PostgreSQL (psycopg2)
- JWT (djangorestframework-simplejwt)

### Разработка
- pytest, pytest-django
- factory-boy для тестовых данных
- ruff для линтинга
- django-debug-toolbar

### Продакшн
- gunicorn
- django-storages (S3/MinIO)
- loguru для логирования

## 🚀 Развертывание

1. **Настройте переменные окружения для продакшена**
2. **Используйте production stage в Dockerfile**
3. **Настройте reverse proxy (nginx)**
4. **Настройте SSL сертификаты**
5. **Настройте мониторинг и логирование**

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 🆘 Поддержка

Если у вас есть вопросы или проблемы:
1. Проверьте [Issues](../../issues)
2. Создайте новый Issue с подробным описанием
3. Обратитесь к документации Django-Ninja

---

**Создано с ❤️ для современной разработки Django API**
