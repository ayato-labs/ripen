import os
import pytest
import aiosqlite
from shared_memory.infra.database import (
    async_get_connection,
    init_db,
    close_all_connections
)

@pytest.mark.asyncio
async def test_database_connection():
    \"\"\"Tests that we can acquire a connection and execute a query.\"\"\"
    # 1. Initialize
    await init_db(force=True)
    
    # 2. Test Connection Lifecycle
    # CORRECT USAGE: async with async_get_connection()
    async with async_get_connection() as conn:
        assert isinstance(conn, aiosqlite.Connection)
        cursor = await conn.execute(\"SELECT 1\")
        row = await cursor.fetchone()
        assert row[0] == 1
    
    await close_all_connections()

@pytest.mark.asyncio
async def test_database_schema():
    \"\"\"Tests that tables are created correctly.\"\"\"
    await init_db(force=True)
    async with async_get_connection() as conn:
        cursor = await conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
        tables = [row[0] for row in await cursor.fetchall()]
        
        expected_tables = [\"entities\", \"graph\", \"observations\", \"bank_files\"]
        for t in expected_tables:
            assert t in tables
            
    await close_all_connections()

@pytest.mark.asyncio
async def test_singleton_persistence():
    \"\"\"Tests that multiple calls return the same connection object.\"\"\"
    await init_db(force=True)
    async with async_get_connection() as conn1:
        async with async_get_connection() as conn2:
            assert conn1 is conn2
            
    await close_all_connections()
