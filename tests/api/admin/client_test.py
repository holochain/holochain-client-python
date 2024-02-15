import pytest
from holochain_client.api.admin.types import (
    AddAdminInterface,
    DnaModifiers,
    InterfaceDriverWebsocket,
    InstallApp,
    RegisterDnaPayloadHash,
    RegisterDnaPayloadPath,
    UpdateCoordinatorsPayloadPath,
)
from holochain_client.api.admin.client import AdminClient
from tests.harness import TestHarness


@pytest.mark.asyncio
async def test_add_admin_interface():
    async with TestHarness() as harness:
        # Get a free port
        import socket

        sock = socket.socket()
        sock.bind(("", 0))
        port = sock.getsockname()[1]
        sock.close()

        await harness.admin_client.add_admin_interfaces(
            [AddAdminInterface(InterfaceDriverWebsocket(port))]
        )

        new_admin_client = await AdminClient.create(f"ws://localhost:{port}")

        agent_pub_key = await new_admin_client.generate_agent_pub_key()
        await new_admin_client.close()
        assert len(agent_pub_key) == 39


@pytest.mark.asyncio
async def test_register_dna():
    async with TestHarness() as harness:
        dna_hash = await harness.admin_client.register_dna(
            RegisterDnaPayloadPath(harness.fixture_dna_path)
        )
        assert len(dna_hash) == 39

        dna_hash_alt = await harness.admin_client.register_dna(
            RegisterDnaPayloadHash(dna_hash, DnaModifiers(network_seed="testing"))
        )
        assert len(dna_hash_alt) == 39
        assert dna_hash != dna_hash_alt


@pytest.mark.asyncio
async def test_get_dna_definition():
    async with TestHarness() as harness:
        dna_hash = await harness.admin_client.register_dna(
            RegisterDnaPayloadPath(harness.fixture_dna_path)
        )
        assert len(dna_hash) == 39

        dna_def = await harness.admin_client.get_dna_definition(dna_hash)
        assert "name" in dna_def
        assert dna_def["name"] == "fixture"


@pytest.mark.asyncio
async def test_update_coordinators():
    async with TestHarness() as harness:
        dna_hash = await harness.admin_client.register_dna(
            RegisterDnaPayloadPath(harness.fixture_dna_path)
        )
        assert len(dna_hash) == 39

        await harness.admin_client.update_coordinators(UpdateCoordinatorsPayloadPath(
            dna_hash,
            harness.fixture_dna_path
        ))

@pytest.mark.asyncio
async def test_install_app():
    async with TestHarness() as harness:
        agent_pub_key = await harness.admin_client.generate_agent_pub_key()

        response = await harness.admin_client.install_app(
            InstallApp(
                agent_key=agent_pub_key,
                installed_app_id="test_app",
                path=harness.fixture_path,
            )
        )

        assert response.installed_app_id == "test_app"


@pytest.mark.asyncio
async def test_list_apps():
    async with TestHarness() as harness:
        agent_pub_key = await harness.admin_client.generate_agent_pub_key()

        await harness.admin_client.install_app(
            InstallApp(
                agent_key=agent_pub_key,
                installed_app_id="test_app",
                path=harness.fixture_path,
            )
        )

        apps = await harness.admin_client.list_apps()
        assert apps[0].agent_pub_key == agent_pub_key
        assert apps[0].installed_app_id == "test_app"


@pytest.mark.asyncio
async def test_attach_app_interface():
    async with TestHarness() as harness:
        app_interface = await harness.admin_client.attach_app_interface()
        assert app_interface.port > 0

        listed = await harness.admin_client.list_app_interfaces()
        assert app_interface.port in listed


@pytest.mark.asyncio
async def test_dump_network_stats():
    async with TestHarness() as harness:
        network_stats = await harness.admin_client.dump_network_stats()
        print("network stats: ", network_stats)
