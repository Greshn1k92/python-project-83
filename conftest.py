import os

import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


@pytest.fixture(autouse=True)
def init_db():
    """Initialize database for tests"""
    # Get DATABASE_URL from environment variables
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        # If DATABASE_URL is not set, use default values for Docker
        database_url = "postgresql://postgres:postgres@db:5432/postgres"

    # Connect to database
    conn = psycopg2.connect(database_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        # Create tables if they don't exist
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

        # Clear tables before each test
        cursor.execute("DELETE FROM url_checks")
        cursor.execute("DELETE FROM urls")

    finally:
        cursor.close()
        conn.close()

    yield

    # Cleanup after test
    conn = psycopg2.connect(database_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM url_checks")
        cursor.execute("DELETE FROM urls")
    finally:
        cursor.close()
        conn.close()
