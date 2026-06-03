"""Unit tests for the serde layer and hashes (no conductor required)."""

from holochain_client.hash import (
    AGENT_PREFIX,
    DNA_PREFIX,
    AgentPubKey,
    DnaHash,
    hash_from_raw,
)
from holochain_client.serde import decode, encode
from holochain_client.types.app import AppDisabled, AppStatus, DisabledByError
from holochain_client.types.capability import (
    CapAccessAssigned,
    GrantedFunctionsAll,
    GrantedFunctionsListed,
)
from holochain_client.types.cell import CellId, CellInfo, ProvisionedCell


def _dna() -> DnaHash:
    return DnaHash(DNA_PREFIX + bytes(32) + bytes(4))


def _agent() -> AgentPubKey:
    return AgentPubKey(AGENT_PREFIX + bytes(32) + bytes(4))


def test_holohash_roundtrip_and_b64():
    dna = _dna()
    assert len(dna) == 39
    assert dna.to_b64().startswith("uhC0k")
    assert DnaHash.from_b64(dna.to_b64()) == dna
    assert isinstance(hash_from_raw(bytes(dna)), DnaHash)


def test_cell_id_serializes_as_pair():
    cell_id = CellId(_dna(), _agent())
    wire = encode(cell_id)
    assert wire == [bytes(_dna()), bytes(_agent())]
    assert decode(wire, CellId) == cell_id


def test_cell_info_provisioned_decode():
    wire = {
        "type": "provisioned",
        "value": {
            "cell_id": [bytes(_dna()), bytes(_agent())],
            "dna_modifiers": {"network_seed": "seed", "properties": None},
            "name": "fixture",
        },
    }
    info = CellInfo.__from_wire__(wire)
    assert isinstance(info, ProvisionedCell)
    assert info.name == "fixture"
    assert info.cell_id == CellId(_dna(), _agent())


def test_app_status_nested_union():
    status = decode(
        {"type": "disabled", "value": {"type": "error", "value": "boom"}}, AppStatus
    )
    assert isinstance(status, AppDisabled)
    assert isinstance(status.reason, DisabledByError)
    assert status.reason.message == "boom"


def test_granted_functions_encode():
    assert encode(GrantedFunctionsAll()) == {"type": "all"}
    assert encode(GrantedFunctionsListed(functions=[["zome", "fn"]])) == {
        "type": "listed",
        "value": [["zome", "fn"]],
    }


def test_cap_access_assigned_encode():
    wire = encode(CapAccessAssigned(secret=bytes(64), assignees=[_agent()]))
    assert wire["type"] == "assigned"
    assert wire["value"]["secret"] == bytes(64)
    assert wire["value"]["assignees"] == [bytes(_agent())]
