import os

import pytest


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ["DATABASE_URL"] = "sqlite:///test_page_analyzer.db"
    os.environ["SECRET_KEY"] = "test-secret-key"
    yield
    # Cleanup
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    if "SECRET_KEY" in os.environ:
        del os.environ["SECRET_KEY"]
