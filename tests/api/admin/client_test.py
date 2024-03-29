import pytest
from holochain_client.api.admin.types import (
    AddAdminInterface,
    DisableApp,
    DnaModifiers,
    EnableApp,
    InterfaceDriverWebsocket,
    InstallApp,
    RegisterDnaPayloadHash,
    RegisterDnaPayloadPath,
    UninstallApp,
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
async def test_uninstall_app():
    async with TestHarness() as harness:
        agent_pub_key = await harness.admin_client.generate_agent_pub_key()

        await harness.admin_client.install_app(
            InstallApp(
                agent_key=agent_pub_key,
                installed_app_id="test_app",
                path=harness.fixture_path,
            )
        )

        assert len(await harness.admin_client.list_apps()) == 1

        await harness.admin_client.uninstall_app(UninstallApp("test_app"))

        assert len(await harness.admin_client.list_apps()) == 0


@pytest.mark.asyncio
async def test_list_dnas():
    async with TestHarness() as harness:
        agent_pub_key = await harness.admin_client.generate_agent_pub_key()

        await harness.admin_client.install_app(
            InstallApp(
                agent_key=agent_pub_key,
                installed_app_id="test_app",
                path=harness.fixture_path,
            )
        )

        assert len(await harness.admin_client.list_dnas()) == 1


@pytest.mark.asyncio
async def test_list_cell_ids():
    async with TestHarness() as harness:
        agent_pub_key = await harness.admin_client.generate_agent_pub_key()

        await harness.admin_client.install_app(
            InstallApp(
                agent_key=agent_pub_key,
                installed_app_id="test_app",
                path=harness.fixture_path,
            )
        )

        # Lists running only, so should be empty before enabling
        cell_ids = await harness.admin_client.list_cell_ids()
        assert len(cell_ids) == 0

        await harness.admin_client.enable_app(EnableApp("test_app"))

        cell_ids = await harness.admin_client.list_cell_ids()
        assert len(cell_ids) == 1
        assert cell_ids[0][0] == (await harness.admin_client.list_dnas())[0]
        assert cell_ids[0][1] == agent_pub_key


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
async def test_enable_and_disable_app():
    async with TestHarness() as harness:
        agent_pub_key = await harness.admin_client.generate_agent_pub_key()

        await harness.admin_client.install_app(
            InstallApp(
                agent_key=agent_pub_key,
                installed_app_id="test_app",
                path=harness.fixture_path,
            )
        )

        app_info = (await harness.admin_client.list_apps())[0]
        assert "disabled" in app_info.status

        await harness.admin_client.enable_app(EnableApp("test_app"))

        app_info = (await harness.admin_client.list_apps())[0]
        assert "running" in app_info.status

        await harness.admin_client.disable_app(DisableApp("test_app"))

        app_info = (await harness.admin_client.list_apps())[0]
        assert "disabled" in app_info.status


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
