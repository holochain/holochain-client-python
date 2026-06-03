"""Admin interface integration tests (require a running conductor)."""

import pytest

from holochain_client.hash import AgentPubKey, DnaHash
from holochain_client.types.app import AppInfo
from holochain_client.types.cell import CellId

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_list_dnas(harness):
    dnas = await harness.admin.list_dnas()
    assert len(dnas) == 1
    assert isinstance(dnas[0], DnaHash)


async def test_list_cell_ids(harness):
    cell_ids = await harness.admin.list_cell_ids()
    assert harness.cell_id in cell_ids
    assert all(isinstance(c, CellId) for c in cell_ids)


async def test_list_apps(harness):
    apps = await harness.admin.list_apps()
    assert any(app.installed_app_id == harness.installed_app_id for app in apps)
    assert all(isinstance(app, AppInfo) for app in apps)


async def test_generate_agent_pub_key(harness):
    key = await harness.admin.generate_agent_pub_key()
    assert isinstance(key, AgentPubKey)
    assert len(key) == 39


async def test_get_dna_definition(harness):
    definition = await harness.admin.get_dna_definition(harness.cell_id)
    assert definition["name"] == "fixture"


async def test_list_app_interfaces(harness):
    interfaces = await harness.admin.list_app_interfaces()
    assert len(interfaces) >= 1
    assert all(i.port > 0 for i in interfaces)
