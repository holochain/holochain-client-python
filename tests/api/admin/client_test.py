import pytest
from holochain_client.api.admin.client import AdminClient
from holochain_client.api.admin.types import (
    AppBundleSourceBundle,
    AppManifest,
    AppRoleDnaManifest,
    AppRoleManifest,
    InstallApp,
)
from tests.harness import TestHarness


@pytest.mark.asyncio
async def test_create():
    async with TestHarness() as harness:
        agent_pub_key = await harness.admin_client.generate_agent_pub_key()

        response = await harness.admin_client.install_app(
            InstallApp(
                agent_key=agent_pub_key,
                installed_app_id="test_app",
                path="/home/thetasinner/source/holo/holochain-client-python/sample.happ",  # TODO
            )
        )
        print("response: ", response)

        assert response.installed_app_id == "test_app"


@pytest.mark.asyncio
async def test_list_apps():
    async with TestHarness() as harness:
        agent_pub_key = await harness.admin_client.generate_agent_pub_key()

        await harness.admin_client.install_app(
            InstallApp(
                agent_key=agent_pub_key,
                installed_app_id="test_app",
                path="/home/thetasinner/source/holo/holochain-client-python/sample.happ",  # TODO
            )
        )

        apps = await harness.admin_client.list_apps()
        assert apps[0].agent_pub_key == agent_pub_key
        assert apps[0].installed_app_id == "test_app"


@pytest.mark.asyncio
async def test_dump_network_stats():
    async with TestHarness() as harness:
        network_stats = await harness.admin_client.dump_network_stats()
        print("network stats: ", network_stats)
