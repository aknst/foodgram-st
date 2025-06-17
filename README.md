# Foodgram

## Описание проекта

Foodgram - это веб-приложение для публикации и поиска рецептов. Пользователи могут создавать, редактировать и удалять свои рецепты, а также подписываться на других авторов и сохранять понравившиеся рецепты.

## Стек технологий

- Python 3.11
- Django 5.0+
- Django REST Framework
- PostgreSQL
- Docker
- Nginx

## Установка и запуск

### Клонирование репозитория

```bash
git clone https://github.com/aknst/foodgram-st.git
```

```bash
cd foodgram-st
```

### Настройка окружения

Создайте файл `.env` в директории `infra`:
```
DEBUG=True

DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=foodgram_db
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=db
DATABASE_PORT=5432

CORS_ORIGIN_ALLOW_ALL=True

SECRET_KEY=secretkey
ALLOWED_HOSTS=localhost,127.0.0.1,host.docker.internal
```

### Локальная установка

1. Установите зависимости:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Примените миграции:
   ```bash
   python manage.py migrate
   ```

3. Импортируйте ингредиенты:
   ```bash
   python manage.py load_ingredients
   ```

4. Запустите сервер:
   ```bash
   python manage.py runserver
   ```

### Установка с помощью Docker

1. Запустите контейнеры:
   ```bash
   cd infra
   docker compose up -d
   ```
   
   После запуска backend-контейнера автоматически выполнится (согласно `docker-compose.yml`):
   - Применение миграций
   - Импорт ингредиентов
   - Сборка статических файлов
   - Запуск сервера на порту 8000

2. Для создания учетной записи администратора необходимо выполнить:
   ```bash
   docker exec -it foodgram-backend bash
   python manage.py createsuperuser
   ```
   
## Доступ к сервисам

После запуска контейнеров доступны следующие сервисы:
- [Frontend](http://localhost:80)
- [Backend](http://localhost:80/api/)
- [Admin панель](http://localhost:80/admin/)
- [API документация](http://localhost:80/api/docs/)

## Автор

Арефьев К. В. — [GitHub](https://github.com/aknst) | [Email](mailto:konstns64@yandex.ru)