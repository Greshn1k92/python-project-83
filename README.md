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
```

## Деплой

Проект настроен для деплоя на render.com. Для деплоя:

1. Создайте аккаунт на [render.com](https://render.com)
2. Создайте новый Web Service
3. Подключите ваш GitHub репозиторий
4. Укажите команду сборки: `make build`
5. Укажите команду запуска: `make render-start`

## Структура проекта

```
page_analyzer/
├── __init__.py      # Экспорт переменной app
├── app.py           # Основное Flask приложение
└── templates/       # HTML шаблоны
    ├── base.html
    ├── index.html
    └── urls.html
```

## Технологии

- Flask - веб-фреймворк
- Gunicorn - WSGI сервер
- Bootstrap - CSS фреймворк
- Ruff - линтер Python кода