import pytest
import pytest_asyncio
import asyncio
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force test database to sqlite in memory or local test db
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key_32_bytes_super_secure_token!"
os.environ["PHONE_HASH_PEPPER"] = "test_pepper_key_2026"

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import async_engine, Base, AsyncSessionLocal

@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    from app.main import seed_initial_defaults
    await seed_initial_defaults()
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
