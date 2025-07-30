import os
import re
import sqlite3

import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Получение соединения с базой данных"""
    database_url = os.getenv("DATABASE_URL")

    # Для локальной разработки используем SQLite
    if not database_url or database_url.startswith("sqlite"):
        return sqlite3.connect("page_analyzer.db")

    # Для продакшена используем PostgreSQL
    return psycopg2.connect(database_url)


def init_db():
    """Инициализация базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Определяем тип базы данных
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            # SQLite схема
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS url_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_id INTEGER REFERENCES urls(id) ON DELETE CASCADE,
                    status_code INTEGER,
                    h1 TEXT,
                    title TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # PostgreSQL схема
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    name varchar(255) NOT NULL UNIQUE,
                    created_at timestamp DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS url_checks (
                    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    url_id bigint REFERENCES urls(id) ON DELETE CASCADE,
                    status_code integer,
                    h1 varchar(255),
                    title varchar(255),
                    description text,
                    created_at timestamp DEFAULT CURRENT_TIMESTAMP
                )
            """)

        conn.commit()
    finally:
        cursor.close()
        conn.close()


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
    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        # Проверяем, существует ли URL
        if is_sqlite:
            cursor.execute("SELECT id FROM urls WHERE name = ?", (url,))
        else:
            cursor.execute("SELECT id FROM urls WHERE name = %s", (url,))

        existing = cursor.fetchone()
        if existing:
            return existing[0]

        # Добавляем новый URL
        if is_sqlite:
            cursor.execute("INSERT INTO urls (name) VALUES (?)", (url,))
            url_id = cursor.lastrowid
        else:
            cursor.execute(
                "INSERT INTO urls (name) VALUES (%s) RETURNING id",
                (url,),
            )
            url_id = cursor.fetchone()[0]

        conn.commit()
        return url_id
    finally:
        cursor.close()
        conn.close()


def get_url_by_id(url_id):
    """Получение URL по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute(
                "SELECT id, name, created_at FROM urls WHERE id = ?",
                (url_id,),
            )
        else:
            cursor.execute(
                "SELECT id, name, created_at FROM urls WHERE id = %s",
                (url_id,),
            )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_all_urls():
    """Получение всех URL с информацией о последней проверке"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            # SQLite не поддерживает LATERAL JOIN, используем подзапрос
            cursor.execute("""
                SELECT u.id, u.name, u.created_at,
                       c.id, c.status_code, c.h1, c.title, c.description, c.created_at
                FROM urls u
                LEFT JOIN (
                    SELECT url_id, id, status_code, h1, title, description, created_at
                    FROM url_checks c1
                    WHERE c1.created_at = (
                        SELECT MAX(c2.created_at)
                        FROM url_checks c2
                        WHERE c2.url_id = c1.url_id
                    )
                ) c ON c.url_id = u.id
                ORDER BY u.created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT u.id, u.name, u.created_at,
                       c.id, c.status_code, c.h1, c.title, c.description, c.created_at
                FROM urls u
                LEFT JOIN LATERAL (
                    SELECT id, status_code, h1, title, description, created_at
                    FROM url_checks
                    WHERE url_id = u.id
                    ORDER BY created_at DESC
                    LIMIT 1
                ) c ON true
                ORDER BY u.created_at DESC
            """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_url_by_name(name):
    """Получение URL по имени"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute(
                "SELECT id, name, created_at FROM urls WHERE name = ?",
                (name,),
            )
        else:
            cursor.execute(
                "SELECT id, name, created_at FROM urls WHERE name = %s",
                (name,),
            )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def _perform_url_check(url):
    """Выполнение проверки URL и извлечение данных"""
    try:
        # Выполняем HTTP-запрос к сайту
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Извлекаем данные из ответа
        status_code = response.status_code
        h1 = None
        title = None
        description = None

        # Парсим HTML для извлечения h1, title и description
        if response.headers.get("content-type", "").startswith("text/html"):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            # Извлекаем h1
            h1_tag = soup.find("h1")
            if h1_tag:
                h1 = h1_tag.get_text().strip()

            # Извлекаем title
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text().strip()

            # Извлекаем description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "").strip()

    except requests.RequestException:
        # Если произошла ошибка при запросе, возвращаем None
        return None
    else:
        return status_code, h1, title, description


def add_check(url_id):
    """Добавление проверки для URL"""
    # Проверяем, что URL существует
    url_data = get_url_by_id(url_id)
    if not url_data:
        return None

    url = url_data[1]

    # Выполняем проверку URL
    result = _perform_url_check(url)
    if result is None:
        return None

    status_code, h1, title, description = result

    # Добавляем новую проверку в базу данных
    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute("""
                INSERT INTO url_checks (url_id, status_code, h1, title, description)
                VALUES (?, ?, ?, ?, ?)
            """, (url_id, status_code, h1, title, description))
            check_id = cursor.lastrowid
        else:
            cursor.execute("""
                INSERT INTO url_checks (url_id, status_code, h1, title, description)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (url_id, status_code, h1, title, description))
            check_id = cursor.fetchone()[0]

        conn.commit()
        return check_id
    finally:
        cursor.close()
        conn.close()


def get_checks_by_url_id(url_id):
    """Получение всех проверок для URL"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute("""
                SELECT id, url_id, status_code, h1, title, description, created_at
                FROM url_checks
                WHERE url_id = ?
                ORDER BY created_at DESC
            """, (url_id,))
        else:
            cursor.execute("""
                SELECT id, url_id, status_code, h1, title, description, created_at
                FROM url_checks
                WHERE url_id = %s
                ORDER BY created_at DESC
            """, (url_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_last_check_by_url_id(url_id):
    """Получение последней проверки для URL"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute("""
                SELECT id, url_id, status_code, h1, title, description, created_at
                FROM url_checks
                WHERE url_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (url_id,))
        else:
            cursor.execute("""
                SELECT id, url_id, status_code, h1, title, description, created_at
                FROM url_checks
                WHERE url_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (url_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
