"""Shared pytest fixtures for integration tests.

This module contains common fixtures used across multiple test files,
including server availability checks and API key management.
"""

import os
from collections.abc import Generator

import pytest
import requests

# Configuration
BASE_URL = os.getenv("EXPT_LOGGER_BASE_URL", "http://localhost:3000")
TEST_EMAIL = "test@cgft.io"
TEST_PASSWORD = "pass1Word2!@"


# ============================================================================
# Helper Functions
# ============================================================================


def check_server_available() -> bool:
    """Check if the logging server is running."""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def _create_api_key(session_cookie: str, name: str) -> tuple[str, str]:
    """Helper to create an API key and return (key, key_id)."""
    response = requests.post(
        f"{BASE_URL}/api/api-keys",
        headers={"Cookie": session_cookie},
        json={"name": name},
        timeout=5,
    )
    assert response.status_code == 201, "Failed to create API key"
    data = response.json()
    return data["key"], data["id"]


def _delete_api_key(session_cookie: str, key_id: str) -> None:
    """Helper to delete an API key."""
    try:
        requests.delete(
            f"{BASE_URL}/api/api-keys",
            headers={"Cookie": session_cookie},
            json={"id": key_id},
            timeout=5,
        )
    except Exception as e:
        print(f"\nWarning: Failed to cleanup API key {key_id}: {e}")


# ============================================================================
# Shared Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def server_available() -> None:
    """Skip tests if server is not available."""
    if not check_server_available():
        pytest.skip(f"Server not available at {BASE_URL}")


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for integration testing."""
    return BASE_URL


@pytest.fixture(scope="session")
def session_cookie(server_available: None) -> str:
    """Create test account and get session cookie.

    This fixture runs once per test session and provides the session cookie
    for creating API keys.
    """
    # Create account (ignore if already exists)
    try:
        requests.post(
            f"{BASE_URL}/api/auth/sign-up/email",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "Test User",
            },
            timeout=5,
        )
    except Exception:
        pass  # Account might already exist

    # Sign in
    response = requests.post(
        f"{BASE_URL}/api/auth/sign-in/email",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
        timeout=5,
    )
    assert response.status_code == 200, "Failed to sign in"

    cookie = response.headers.get("set-cookie")
    assert cookie, "No session cookie received"
    return cookie


@pytest.fixture(scope="session")
def shared_api_key(session_cookie: str) -> Generator[str, None, None]:
    """Create session-scoped API key and clean it up after all tests.

    This fixture runs once per test session and provides a shared API key
    for all integration tests. The key is deleted at the end of the session.
    """
    key, key_id = _create_api_key(session_cookie, "Integration Test Key (Session)")

    yield key

    # Cleanup: Delete the API key
    _delete_api_key(session_cookie, key_id)
    print(f"\nCleaned up session API key: {key_id}")
