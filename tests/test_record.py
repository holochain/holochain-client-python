"""Unit tests for Record/Action/Entry decoding (no conductor required)."""

import msgpack

from holochain_client.hash import (
    ACTION_PREFIX,
    AGENT_PREFIX,
    ENTRY_PREFIX,
    ActionHash,
    AgentPubKey,
)
from holochain_client.types.record import (
    AppEntry,
    Create,
    EntryPresent,
    EntryTypeApp,
    decode_record,
)


def _hash(prefix):
    return prefix + bytes(32) + bytes(4)


def _create_record():
    action_hash = _hash(ACTION_PREFIX)
    return {
        "signed_action": {
            "hashed": {
                "hash": action_hash,
                "content": {
                    "type": "Create",
                    "author": _hash(AGENT_PREFIX),
                    "timestamp": 1700000000000000,
                    "action_seq": 5,
                    "prev_action": action_hash,
                    "entry_type": {
                        "App": {
                            "entry_index": 0,
                            "zome_index": 1,
                            "visibility": "Public",
                        }
                    },
                    "entry_hash": _hash(ENTRY_PREFIX),
                    "weight": {"bucket_id": 0, "units": 0},
                },
            },
            "signature": bytes(64),
        },
        "entry": {
            "Present": {
                "entry_type": "App",
                "entry": msgpack.packb({"value": "first"}, use_bin_type=True),
            }
        },
    }


def test_decode_record_action_is_typed():
    record = decode_record(_create_record())
    action = record.action()
    assert isinstance(action, Create)
    assert isinstance(action.author, AgentPubKey)
    assert action.action_seq == 5
    assert isinstance(record.action_hash(), ActionHash)


def test_decode_record_internal_external_adjacent_tagging():
    record = decode_record(_create_record())
    # internal-tagged Action -> external-tagged EntryType -> nested struct.
    assert isinstance(record.action().entry_type, EntryTypeApp)
    assert record.action().entry_type.app_entry_def.zome_index == 1


def test_decode_record_entry_roundtrips():
    record = decode_record(_create_record())
    assert isinstance(record.entry, EntryPresent)
    entry = record.entry_value()
    assert isinstance(entry, AppEntry)
    assert msgpack.unpackb(entry.bytes, raw=False) == {"value": "first"}
