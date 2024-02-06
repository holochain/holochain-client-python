import pytest
from holochain_client.api.admin.client import AdminClient
from tests.harness import TestHarness, start_holochain
import subprocess

@pytest.mark.asyncio
async def test_connect():
    async with TestHarness() as harness:
        client = await AdminClient.create("ws://localhost:8888")
        await client.close()        
