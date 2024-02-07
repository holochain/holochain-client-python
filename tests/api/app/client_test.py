import pytest
from holochain_client.api.app.client import AppClient
from holochain_client.api.admin.types import (
    InstallApp,
)
from tests.harness import TestHarness


@pytest.mark.asyncio
async def test_call_zome():
    async with TestHarness() as harness:
        agent_pub_key = await harness.admin_client.generate_agent_pub_key()

        await harness.admin_client.install_app(
            InstallApp(
                agent_key=agent_pub_key,
                installed_app_id="test_app",
                path=harness.fixture_path,
            )
        )

        await harness.app_client.call_zome()
