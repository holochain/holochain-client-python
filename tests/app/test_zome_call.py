"""App interface and zome-call integration tests (require a running conductor)."""

import asyncio

import msgpack
import pytest

from holochain_client.hash import ActionHash
from holochain_client.types.record import AppEntry, Create, decode_record

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_echo(harness):
    result = await harness.app.call_zome(harness.cell_id, "fixture", "echo", "hello")
    assert result == "hello"


async def test_app_info(harness):
    info = await harness.app.app_info()
    assert info is not None
    assert info.installed_app_id == harness.installed_app_id
    assert "fixture" in info.cell_info


async def test_create_and_get_fixture(harness):
    raw = await harness.app.call_zome(
        harness.cell_id, "fixture", "create_fixture", {"value": "first"}
    )
    # The created Record decodes into typed Action/Entry models.
    record = decode_record(raw)
    assert isinstance(record.action(), Create)
    assert isinstance(record.action_hash(), ActionHash)
    entry = record.entry_value()
    assert isinstance(entry, AppEntry)
    assert msgpack.unpackb(entry.bytes, raw=False) == {"value": "first"}

    fetched = decode_record(
        await harness.app.call_zome(
            harness.cell_id, "fixture", "get_fixture", record.action_hash()
        )
    )
    assert fetched.action_hash() == record.action_hash()


async def test_get_all_fixtures(harness):
    await harness.app.call_zome(
        harness.cell_id, "fixture", "create_fixture", {"value": "linked"}
    )
    links = await harness.app.call_zome(
        harness.cell_id, "fixture", "get_all_fixtures", None
    )
    assert isinstance(links, list)
    assert len(links) >= 1


async def test_signal_delivery(harness):
    received: asyncio.Queue = asyncio.Queue()
    harness.app.on_signal(lambda signal: received.put_nowait(signal))

    await harness.app.call_zome(harness.cell_id, "fixture", "emit", "ping")

    signal = await asyncio.wait_for(received.get(), timeout=10)
    assert signal.payload["value"] == "ping"
