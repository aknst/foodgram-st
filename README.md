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

### Локальная установка

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Создайте файл `.env` в директории `backend`:
   ```
   DATABASE_NAME=foodgram
   DATABASE_USER=postgres
   DATABASE_PASSWORD=postgres
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   ```

3. Примените миграции:
   ```bash
   python manage.py migrate
   ```

4. Запустите сервер:
   ```bash
   python manage.py runserver
   ```

### Установка с помощью Docker

1. Установите Docker и Docker Compose

2. Создайте файл `.env` в директории `infra`:
   ```
   DATABASE_NAME=foodgram
   DATABASE_USER=postgres
   DATABASE_PASSWORD=postgres
   DATABASE_PORT=5432
   ```

3. Запустите контейнеры:
   ```bash
   docker-compose up -d
   ```

4. После запуска контейнеров, проверьте статус:
   ```bash
   docker-compose ps
   ```
   
## Доступ к сервисам

После запуска контейнеров:
- Frontend: http://localhost:80
- Backend: http://localhost:80/api/
- API документация: http://localhost:80/api/docs/
- Admin панель: http://localhost:80/admin/

## Обслуживание

### Остановка сервисов

```bash
docker-compose down
```

### Перезапуск сервисов

```bash
docker-compose restart
```

### Просмотр логов

```bash
docker-compose logs -f
```