import pytest
from holochain_client.api.admin.client import AdminClient
from tests.harness import TestHarness

@pytest.mark.asyncio
async def test_list_apps():
    async with TestHarness() as harness:
        apps = await harness.admin_client.list_apps()
        print("apps: ", apps)

@pytest.mark.asyncio
async def test_dump_network_stats():
    async with TestHarness() as harness:
        network_stats = await harness.admin_client.dump_network_stats()
        print("network stats: ", network_stats)
