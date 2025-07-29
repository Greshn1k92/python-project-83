import psycopg2
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
import validators

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')


def get_db_connection():
    """Получение соединения с базой данных"""
    return psycopg2.connect(DATABASE_URL)


def validate_url(url):
    """Валидация URL"""
    if not url:
        return False, "URL обязателен"
    
    if len(url) > 255:
        return False, "URL превышает 255 символов"
    
    if not validators.url(url):
        return False, "Некорректный URL"
    
    return True, ""


def add_url(url):
    """Добавление URL в базу данных"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO urls (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id",
                (url,)
            )
            result = cur.fetchone()
            conn.commit()
            return result[0] if result else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_url_by_id(url_id):
    """Получение URL по ID"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (url_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_all_urls():
    """Получение всех URL, отсортированных по дате создания (новые первые)"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls ORDER BY created_at DESC")
            return cur.fetchall()
    finally:
        conn.close()


def get_url_by_name(name):
    """Получение URL по имени"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls WHERE name = %s", (name,))
            return cur.fetchone()
    finally:
        conn.close() 