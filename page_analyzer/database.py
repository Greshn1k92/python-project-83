import os
import re
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

# Временное хранилище для демонстрации (в продакшене будет PostgreSQL)
_urls_storage = []
_next_id = 1


def validate_url(url):
    """Валидация URL"""
    if not url:
        return False, "URL обязателен"

    if len(url) > 255:
        return False, "URL превышает 255 символов"

    # Простая валидация URL
    url_pattern = re.compile(
        r"^https?://"  # http:// или https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # домен
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
        r"(?::\d+)?"  # порт
        r"(?:/?|[/?]\S+)$", re.IGNORECASE)

    if not url_pattern.match(url):
        return False, "Некорректный URL"

    return True, ""


def add_url(url):
    """Добавление URL в базу данных"""
    global _next_id

    # Проверяем, существует ли URL
    for existing_url in _urls_storage:
        if existing_url[1] == url:
            return existing_url[0]

    # Добавляем новый URL
    url_id = _next_id
    _next_id += 1

    _urls_storage.append((url_id, url, datetime.now(timezone.utc)))
    return url_id


def get_url_by_id(url_id):
    """Получение URL по ID"""
    for url_data in _urls_storage:
        if url_data[0] == url_id:
            return url_data
    return None


def get_all_urls():
    """Получение всех URL, отсортированных по дате создания (новые первые)"""
    return sorted(_urls_storage, key=lambda x: x[2], reverse=True)


def get_url_by_name(name):
    """Получение URL по имени"""
    for url_data in _urls_storage:
        if url_data[1] == name:
            return url_data
    return None
