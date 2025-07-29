import os
import re
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

# Временное хранилище для демонстрации (в продакшене будет PostgreSQL)
_urls_storage = []
_checks_storage = []
_next_id = 1
_next_check_id = 1


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
    """Получение всех URL с информацией о последней проверке"""
    urls_with_checks = []
    for url_data in _urls_storage:
        last_check = get_last_check_by_url_id(url_data[0])
        urls_with_checks.append((url_data[0], url_data[1], url_data[2], last_check))
    return sorted(urls_with_checks, key=lambda x: x[2], reverse=True)


def get_url_by_name(name):
    """Получение URL по имени"""
    for url_data in _urls_storage:
        if url_data[1] == name:
            return url_data
    return None


def add_check(url_id):
    """Добавление проверки для URL"""
    global _next_check_id

    # Проверяем, что URL существует
    url_exists = any(url_data[0] == url_id for url_data in _urls_storage)
    if not url_exists:
        return None

    # Добавляем новую проверку
    check_id = _next_check_id
    _next_check_id += 1

    check_data = (check_id, url_id, None, None, None, None, datetime.now(timezone.utc))
    _checks_storage.append(check_data)
    return check_id


def get_checks_by_url_id(url_id):
    """Получение всех проверок для URL"""
    checks = [check_data for check_data in _checks_storage if check_data[1] == url_id]
    return sorted(checks, key=lambda x: x[6], reverse=True)  # Сортировка по дате создания


def get_last_check_by_url_id(url_id):
    """Получение последней проверки для URL"""
    checks = get_checks_by_url_id(url_id)
    return checks[0] if checks else None
