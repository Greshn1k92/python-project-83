# Анализатор страниц

Веб-приложение для анализа веб-страниц на SEO пригодность.

## Установка

```bash
make install
```

## Разработка

Для запуска в режиме разработки:

```bash
make dev
```

Приложение будет доступно по адресу http://localhost:5000

## Продакшн

Для запуска в продакшене:

```bash
make start
```

Приложение будет доступно по адресу http://localhost:8000

## Переменные окружения

Создайте файл `.env` в корне проекта:

```
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
DATABASE_URL=postgres://postgres:password@localhost:5432/page_analyzer
```

## Деплой на render.com

Проект настроен для деплоя на render.com. Для деплоя:

1. Создайте аккаунт на [render.com](https://render.com)
2. Создайте новый Web Service
3. Подключите ваш GitHub репозиторий: `https://github.com/Greshn1k92/python-project-83`
4. Укажите команду сборки: `make build`
5. Укажите команду запуска: `make render-start`
6. Добавьте переменную окружения `DATABASE_URL` с вашей PostgreSQL базой данных

## База данных

Для локальной разработки используйте PostgreSQL. Создайте базу данных и выполните SQL из файла `database.sql`:

```sql
CREATE TABLE urls (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(255) NOT NULL UNIQUE,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP
);
```

## Структура проекта

```
page_analyzer/
├── __init__.py      # Экспорт переменной app
├── app.py           # Основное Flask приложение
├── database.py      # Работа с базой данных
└── templates/       # HTML шаблоны
    ├── base.html
    ├── index.html
    ├── urls.html
    └── url_show.html
```

## Функциональность

- ✅ Валидация URL (максимум 255 символов)
- ✅ Добавление URL в базу данных
- ✅ Просмотр списка всех URL
- ✅ Просмотр конкретного URL по ID
- ✅ Предотвращение дублирования URL
- ✅ Flash-сообщения об ошибках и успехе

## Технологии

- Flask - веб-фреймворк
- Gunicorn - WSGI сервер
- Bootstrap - CSS фреймворк
- PostgreSQL - база данных
- Ruff - линтер Python кода