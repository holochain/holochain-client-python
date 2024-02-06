import pytest
from holochain_client.api.admin.client import AdminClient
from tests.harness import TestHarness, start_holochain
import subprocess

@pytest.mark.asyncio
async def test_connect():
    async with TestHarness() as harness:
        print("harness.admin_client: ", harness.admin_client)
