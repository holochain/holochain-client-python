import pytest
from holochain_client.api.app.client import AppClient
from holochain_client.api.admin.types import (
    EnableApp,
    InstallApp,
)
from holochain_client.api.app.types import ZomeCallUnsigned
from holochain_client.api.common.signing import authorize_signing_credentials
from tests.harness import TestHarness
import msgpack


@pytest.mark.asyncio
async def test_call_zome():
    async with TestHarness() as harness:
        agent_pub_key = await harness.admin_client.generate_agent_pub_key()

        app_info = await harness.admin_client.install_app(
            InstallApp(
                agent_key=agent_pub_key,
                installed_app_id="test_app",
                path=harness.fixture_path,
            )
        )

        await harness.admin_client.enable_app(EnableApp(app_info.installed_app_id))

        cell_id = app_info.cell_info["fixture"][0]["provisioned"]["cell_id"]
        await authorize_signing_credentials(harness.admin_client, cell_id)

        await harness.app_client.call_zome(
            ZomeCallUnsigned(
                cell_id=cell_id,
                zome_name="fixture",
                fn_name="create_fixture",
                payload=msgpack.packb({"name": "hello fixture"}),
            )
        )
