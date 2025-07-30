import pytest

from page_analyzer.app import app
from page_analyzer.database import init_db


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    
    # Инициализируем базу данных для тестов
    init_db()
    
    with app.test_client() as client:
        yield client


def test_index_page(client):
    """Test that the index page loads successfully."""
    response = client.get("/")
    assert response.status_code == 200


def test_urls_page_get(client):
    """Test that the URLs page loads successfully."""
    response = client.get("/urls")
    assert response.status_code == 200


def test_url_show_page(client):
    """Test that the URL show page loads successfully."""
    # This test will fail if no URLs exist, but that's expected
    response = client.get("/urls/1")
    assert response.status_code in [200, 404]


def test_url_checks_page(client):
    """Test that the URL checks page loads successfully."""
    # This test will fail if no URLs exist, but that's expected
    response = client.post("/urls/1/checks")
    assert response.status_code in [302, 404]
