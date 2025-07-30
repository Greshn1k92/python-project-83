import os

import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


@pytest.fixture(autouse=True)
def init_db():
    """Инициализация базы данных для тестов"""
    # Получаем DATABASE_URL из переменных окружения
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        # Если DATABASE_URL не задан, используем значения по умолчанию для Docker
        database_url = "postgresql://postgres:postgres@db:5432/postgres"

    # Подключаемся к базе данных
    conn = psycopg2.connect(database_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        # Создаем таблицы если их нет
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

        # Очищаем таблицы перед каждым тестом
        cursor.execute("DELETE FROM url_checks")
        cursor.execute("DELETE FROM urls")

    finally:
        cursor.close()
        conn.close()

    yield

    # Очистка после теста
    conn = psycopg2.connect(database_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM url_checks")
        cursor.execute("DELETE FROM urls")
    finally:
        cursor.close()
        conn.close()
