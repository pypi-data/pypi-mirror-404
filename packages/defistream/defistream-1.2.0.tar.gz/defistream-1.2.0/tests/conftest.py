"""
Shared fixtures for DeFiStream python-client integration tests.

Mirrors the API test suite conftest at api/tests/api-gateway/decoders/conftest.py,
adapted for the python-client's builder-pattern interface.

Run with:
    python -m pytest tests/test_integration.py -v
    python -m pytest tests/test_integration.py -v --local   # local dev gateway
"""

import os
import sys
from pathlib import Path

import pytest

from defistream import AsyncDeFiStream, DeFiStream

# ---------------------------------------------------------------------------
# --local flag support
# ---------------------------------------------------------------------------

_local_mode = "--local" in sys.argv

_PRODUCTION_URL = "https://api.defistream.dev/v1"
_LOCAL_URL = "http://localhost:8081/v1"


def pytest_addoption(parser):
    parser.addoption(
        "--local",
        action="store_true",
        default=False,
        help="Test against local dev gateway (http://localhost:8081/v1) instead of production",
    )


# ---------------------------------------------------------------------------
# .env loading
# ---------------------------------------------------------------------------

def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        env[key] = value
    return env


def _get_env() -> dict[str, str]:
    env = dict(os.environ)
    project_root = Path(__file__).resolve().parents[1]  # python-client/
    repo_root = project_root.parent                      # DeFiStream/
    for candidate in [project_root / ".env", repo_root / ".env"]:
        for key, value in _load_env_file(candidate).items():
            if key not in env:
                env[key] = value
    return env


_env = _get_env()

# ---------------------------------------------------------------------------
# Resolved configuration
# ---------------------------------------------------------------------------

API_BASE_URL = _LOCAL_URL if _local_mode else _env.get("API_BASE_URL", _PRODUCTION_URL).rstrip("/")
TEST_API_KEY = _env.get("TEST_API_KEY", "")

# ---------------------------------------------------------------------------
# Auto-skip integration tests when API key is missing
# ---------------------------------------------------------------------------

_skip_no_key = pytest.mark.skipif(
    not TEST_API_KEY,
    reason="TEST_API_KEY not set in environment or .env",
)


def pytest_collection_modifyitems(config, items):
    """Skip integration tests automatically when TEST_API_KEY is absent."""
    for item in items:
        if "test_integration" in str(item.fspath):
            item.add_marker(_skip_no_key)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    """Sync DeFiStream client shared across a test module."""
    c = DeFiStream(api_key=TEST_API_KEY, base_url=API_BASE_URL)
    yield c
    c.close()


@pytest.fixture
async def async_client():
    """Async DeFiStream client — function-scoped for a clean event loop."""
    c = AsyncDeFiStream(api_key=TEST_API_KEY, base_url=API_BASE_URL)
    yield c
    await c.close()
