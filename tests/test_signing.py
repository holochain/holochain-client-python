"""Unit tests for zome-call signing (no conductor required)."""

import hashlib

import msgpack
from nacl.signing import VerifyKey

from holochain_client.hash import AGENT_PREFIX, DNA_PREFIX, AgentPubKey, DnaHash
from holochain_client.signing import SigningKeyPair, sign_zome_call
from holochain_client.types.cell import CellId


def test_signing_key_agent_pub_key_layout():
    keypair = SigningKeyPair()
    agent = keypair.agent_pub_key
    assert isinstance(agent, AgentPubKey)
    assert len(agent) == 39
    assert bytes(agent[:3]) == AGENT_PREFIX
    assert bytes(agent[-4:]) == bytes(4)  # zeroed location


def test_sign_zome_call_is_verifiable():
    keypair = SigningKeyPair()
    cell_id = CellId(
        DnaHash(DNA_PREFIX + bytes(32) + bytes(4)),
        keypair.agent_pub_key,
    )
    signed = sign_zome_call(
        cell_id=cell_id,
        zome_name="fixture",
        fn_name="echo",
        payload="hello",
        provenance=keypair.agent_pub_key,
        signing_key=keypair,
        cap_secret=bytes(64),
    )
    # The signature is over the SHA-512 of the transmitted bytes.
    expected_hash = hashlib.sha512(signed.bytes).digest()
    verify_key = VerifyKey(bytes(keypair.agent_pub_key[3:35]))
    verify_key.verify(expected_hash, signed.signature)

    # The transmitted bytes deserialize back to the params, with a
    # double-encoded payload.
    params = msgpack.unpackb(signed.bytes, raw=False)
    assert params["zome_name"] == "fixture"
    assert params["fn_name"] == "echo"
    assert msgpack.unpackb(params["payload"], raw=False) == "hello"
    assert len(params["nonce"]) == 32
