import os
import shutil
import tempfile
import time
from contextlib import contextmanager
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
async def setup_teardown_db(request):
    from loguru import logger

    from ripen.core.thought_logic import init_thoughts_db
    from ripen.infra.database import close_all_connections, init_db

    # Windows Fix: Clear loguru handlers before test to prevent WinError 32 on rotation
    logger.remove()

    # Standard path resolution for testing - Use a more specific prefix
    home_dir = tempfile.mkdtemp(prefix="sm_test_")
    os.environ["SHARED_MEMORY_HOME"] = home_dir
    os.environ["MEMORY_DB_PATH"] = os.path.join(home_dir, "knowledge.db")
    os.environ["THOUGHTS_DB_PATH"] = os.path.join(home_dir, "thoughts.db")
    os.environ["MEMORY_BANK_DIR"] = os.path.join(home_dir, "bank")

    # Force reset settings cache to pick up new environment variables
    from ripen.common.config import settings
    settings._base_dir = None
    settings._api_key = None
    settings._config_data = {}

    # Load global config.json api key if GEMINI_API_KEY is not set or is a placeholder
    curr_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not curr_key or "your_gemini_api_key_here" in curr_key:
        global_home = os.path.expanduser("~/.ripen")
        global_config_path = os.path.join(global_home, "config.json")
        if os.path.exists(global_config_path):
            try:
                import json
                with open(global_config_path, encoding="utf-8") as f:
                    config_data = json.load(f)
                    api_key = config_data.get("google_api_key") or config_data.get("gemini_api_key")
                    if api_key and "your_gemini_api_key_here" not in api_key:
                        os.environ["GEMINI_API_KEY"] = api_key
            except Exception:
                pass


    # Initialize databases for each test (Skip for system tests to avoid locking)
    if "system" not in str(request.node.fspath):
        from ripen.infra.database import close_all_connections, init_db
        await close_all_connections()
        await init_db(force=True)
        await init_thoughts_db(force=True)

        # Reset server initialization state
        from ripen.api import server

        server._INITIALIZED_EVENT = None
        server._INIT_ERROR = None
        server._INIT_STARTED = False
        server._INIT_LOCK = None
    else:
        # Still need to create the directory so env vars point to a valid place
        os.makedirs(os.environ["MEMORY_BANK_DIR"], exist_ok=True)

    yield

    # Teardown: Close singleton connections before rmtree (Windows requirement)
    try:
        from ripen.api.server import wait_for_background_tasks
        from ripen.infra.database import close_all_connections

        await wait_for_background_tasks(timeout=2.0)
        await close_all_connections()
    except Exception as e:
        print(f"DEBUG: Teardown close_all_connections failed: {e}")

    if os.path.exists(home_dir):
        # Retry logic for Windows rmtree
        for _ in range(10):
            try:
                shutil.rmtree(home_dir, ignore_errors=False)
                break
            except OSError:
                time.sleep(0.2)


@pytest.fixture
def fake_llm_client():
    """Deterministic LLM stub for Unit Tests (No MagicMock)."""
    from ripen.infra.llm import LlmProvider
    from tests.unit.fake_client import FakeGeminiClient

    client = FakeGeminiClient()

    # Wrap client to behave like LlmProvider if needed
    class FakeProvider(LlmProvider):
        async def generate_content(self, prompt: str, system_instruction: str | None = None) -> str:
            resp = client.models.generate_content(model="fake", contents=prompt)
            return resp.text

        async def check_health(self) -> bool:
            return True

    provider = FakeProvider()

    patches = [
        patch("ripen.infra.llm.get_llm_provider", return_value=provider),
        patch("ripen.infra.embeddings.get_gemini_client", return_value=client),
    ]

    for p in patches:
        p.start()

    try:
        yield client
    finally:
        for p in patches:
            p.stop()


@pytest.fixture
def fake_llm(fake_llm_client):
    """Alias for fake_llm_client for backward compatibility."""
    return fake_llm_client


@contextmanager
def temp_env(env_vars):
    old_env = os.environ.copy()
    os.environ.update(env_vars)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_env)


@pytest.fixture
async def uow():
    """Provides a UnitOfWork for the test database."""
    from ripen.infra.uow import UnitOfWork

    async with UnitOfWork() as uow:
        yield uow


@pytest.fixture
async def db_conn(uow):
    """Provides a connection to the test database via UoW."""
    yield uow._conn
