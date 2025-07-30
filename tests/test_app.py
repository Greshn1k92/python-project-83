import pytest

from page_analyzer.app import app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
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


def test_invalid_url_validation(client):
    """Test URL validation with invalid URL."""
    response = client.post("/urls", data={"url": "invalid-url"})
    assert response.status_code == 422


def test_empty_url_validation(client):
    """Test URL validation with empty URL."""
    response = client.post("/urls", data={"url": ""})
    assert response.status_code == 422


def test_long_url_validation(client):
    """Test URL validation with URL longer than 255 characters."""
    long_url = "http://example.com/" + "a" * 250
    response = client.post("/urls", data={"url": long_url})
    assert response.status_code == 422
