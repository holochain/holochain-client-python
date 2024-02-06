from holochain_client.api.admin.signing import authorize_signing_credentials, generate_signing_keypair
import pytest
from holochain_client.api.admin.types import EnableApp, InstallApp

from tests.harness import TestHarness

def test_generate_signing_keypair():
    signing_keypair = generate_signing_keypair()
    assert len(signing_keypair.identity) == 39

@pytest.mark.asyncio
async def test_authorize_signing_credentials():
    async with TestHarness() as harness:
        agent_pub_key = await harness.admin_client.generate_agent_pub_key()

        response = await harness.admin_client.install_app(
            InstallApp(
                agent_key=agent_pub_key,
                installed_app_id="test_app",
                path=harness.fixture_path,
            )
        )
        print("response: ", response)

        await harness.admin_client.enable_app(EnableApp(installed_app_id=response.installed_app_id))

        await authorize_signing_credentials(harness.admin_client, response.cell_info["fixture"][0]["provisioned"]["cell_id"], None)

        assert response.installed_app_id == "test_app"

