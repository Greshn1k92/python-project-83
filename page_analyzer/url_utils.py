import re
from urllib.parse import urlparse, urlunparse

# Constants
MAX_URL_LENGTH = 255


def normalize_url(url):
    """Normalize URL to scheme + netloc
    (ignore path, params, query, fragment)
    """
    parsed = urlparse(url)
    normalized = urlunparse((
        parsed.scheme, parsed.netloc, '', '', '', ''
    ))
    return normalized


def validate_url(url):
    """Validate URL"""
    if not url:
        return False, "URL обязателен"

    if len(url) > MAX_URL_LENGTH:
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
