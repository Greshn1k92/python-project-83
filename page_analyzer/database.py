import os
import sqlite3

import psycopg2
from dotenv import load_dotenv

from .page_parser import parse_page
from .url_utils import normalize_url

load_dotenv()


def get_connection():
    """Get database connection"""
    database_url = os.getenv("DATABASE_URL")

    # Для локальной разработки используем SQLite
    if not database_url or database_url.startswith("sqlite"):
        return sqlite3.connect("page_analyzer.db")

    # Для продакшена используем PostgreSQL
    return psycopg2.connect(database_url)


def init_db():
    """Initialize database"""
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


def add_url(url):
    """Add URL to database"""
    # Нормализуем URL
    normalized_url = normalize_url(url)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Проверяем, существует ли URL
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute(
                "SELECT id FROM urls WHERE name = ?", (normalized_url,)
            )
        else:
            cursor.execute(
                "SELECT id FROM urls WHERE name = %s", (normalized_url,)
            )

        existing = cursor.fetchone()
        if existing:
            return existing[0]

        # Добавляем новый URL
        if is_sqlite:
            cursor.execute(
                "INSERT INTO urls (name) VALUES (?)", (normalized_url,)
            )
            url_id = cursor.lastrowid
        else:
            cursor.execute(
                "INSERT INTO urls (name) VALUES (%s) RETURNING id",
                (normalized_url,),
            )
            url_id = cursor.fetchone()[0]

        conn.commit()
        return url_id
    finally:
        cursor.close()
        conn.close()


def get_url_by_id(url_id):
    """Get URL by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute("SELECT * FROM urls WHERE id = ?", (url_id,))
        else:
            cursor.execute("SELECT * FROM urls WHERE id = %s", (url_id,))

        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_all_urls():
    """Get all URLs with last check information"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute("""
                SELECT
                    u.id, u.name, u.created_at,
                    lc.status_code, lc.created_at as last_check_date
                FROM urls u
                LEFT JOIN (
                    SELECT url_id, status_code, created_at,
                           ROW_NUMBER() OVER (
                               PARTITION BY url_id ORDER BY created_at DESC
                           ) as rn
                    FROM url_checks
                ) lc ON u.id = lc.url_id AND lc.rn = 1
                ORDER BY u.created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT
                    u.id, u.name, u.created_at,
                    lc.status_code, lc.created_at as last_check_date
                FROM urls u
                LEFT JOIN (
                    SELECT url_id, status_code, created_at,
                           ROW_NUMBER() OVER (
                               PARTITION BY url_id ORDER BY created_at DESC
                           ) as rn
                    FROM url_checks
                ) lc ON u.id = lc.url_id AND lc.rn = 1
                ORDER BY u.created_at DESC
            """)

        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_url_by_name(name):
    """Get URL by name"""
    # Нормализуем URL
    normalized_name = normalize_url(name)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute(
                "SELECT * FROM urls WHERE name = ?", (normalized_name,)
            )
        else:
            cursor.execute(
                "SELECT * FROM urls WHERE name = %s", (normalized_name,)
            )

        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def add_check(url_id):
    """Add URL check to database"""
    # Получаем URL для проверки
    url_data = get_url_by_id(url_id)
    if not url_data:
        return None

    url = url_data[1]  # name field

    # Выполняем проверку
    check_data = parse_page(url)
    if not check_data:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute(
                "INSERT INTO url_checks"
                "(url_id, status_code, h1, title, description) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    url_id, check_data["status_code"], check_data["h1"],
                    check_data["title"], check_data["description"]
                ),
            )
            check_id = cursor.lastrowid
        else:
            cursor.execute(
                "INSERT INTO url_checks"
                "(url_id, status_code, h1, title, description) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (
                    url_id, check_data["status_code"], check_data["h1"],
                    check_data["title"], check_data["description"]
                ),
            )
            check_id = cursor.fetchone()[0]

        conn.commit()
        return check_id
    finally:
        cursor.close()
        conn.close()


def get_checks_by_url_id(url_id):
    """Get all checks for URL"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute(
                "SELECT * FROM url_checks WHERE url_id = ? "
                "ORDER BY created_at DESC",
                (url_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM url_checks WHERE url_id = %s "
                "ORDER BY created_at DESC",
                (url_id,),
            )

        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_last_check_by_url_id(url_id):
    """Get last check for URL"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)

        if is_sqlite:
            cursor.execute(
                "SELECT * FROM url_checks WHERE url_id = ? "
                "ORDER BY created_at DESC LIMIT 1",
                (url_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM url_checks WHERE url_id = %s "
                "ORDER BY created_at DESC LIMIT 1",
                (url_id,),
            )

        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
