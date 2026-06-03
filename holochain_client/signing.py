"""Client-side zome-call signing.

Holochain authorizes zome calls with an ephemeral ed25519 *signing key* (not the
agent's real key) that has been granted a capability on the conductor. To sign a
call we serialize the :class:`ZomeCallParams` with MessagePack, SHA-512 the
bytes, sign the hash, and transmit ``{bytes, signature}`` — the conductor
verifies by hashing the bytes it received, so our encoding need only round-trip
through its ``serde`` deserializer.
"""

from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass
from typing import Dict, Optional

from nacl.signing import SigningKey

from .hash import AGENT_PREFIX, AgentPubKey
from .serde import encode
from .types.cell import CellId
from .types.common import CapSecret

# Zome calls expire 5 minutes after signing, matching the JS client.
NONCE_EXPIRY_SECONDS = 5 * 60


class SigningKeyPair:
    """An ephemeral ed25519 keypair plus its Holochain ``AgentPubKey`` form."""

    def __init__(self, signing_key: Optional[SigningKey] = None):
        self._signing_key = signing_key or SigningKey.generate()
        public_key = bytes(self._signing_key.verify_key)
        # A signing key is presented to Holochain as a 39-byte AgentPubKey:
        # the agent prefix, the 32-byte public key, and a zeroed DHT location
        # (the location is irrelevant for a signing-only identity).
        self.agent_pub_key = AgentPubKey(AGENT_PREFIX + public_key + bytes(4))

    def sign(self, data: bytes) -> bytes:
        """Return the 64-byte detached ed25519 signature of ``data``."""
        return self._signing_key.sign(data).signature


@dataclass
class SigningCredentials:
    """Credentials authorizing zome calls for a single cell."""

    cap_secret: CapSecret
    signing_key: SigningKeyPair


def random_cap_secret() -> CapSecret:
    return secrets.token_bytes(64)


def random_nonce() -> bytes:
    return secrets.token_bytes(32)


def nonce_expires_at() -> int:
    """Expiry timestamp in microseconds since the Unix epoch."""
    return (int(time.time() * 1000) + NONCE_EXPIRY_SECONDS * 1000) * 1000


@dataclass
class SignedZomeCall:
    """The ``ZomeCallParamsSigned`` payload sent to the conductor."""

    bytes: bytes
    signature: bytes


def sign_zome_call(
    *,
    cell_id: CellId,
    zome_name: str,
    fn_name: str,
    payload: object,
    provenance: AgentPubKey,
    signing_key: SigningKeyPair,
    cap_secret: Optional[CapSecret],
    nonce: Optional[bytes] = None,
    expires_at: Optional[int] = None,
) -> SignedZomeCall:
    """Serialize and sign a set of zome-call parameters.

    ``payload`` is the (already application-shaped) zome input; it is itself
    MessagePack-encoded before being embedded in the params, matching Holochain's
    ``ExternIO`` field.
    """
    import msgpack

    params = {
        "provenance": bytes(provenance),
        "cell_id": [bytes(cell_id.dna_hash), bytes(cell_id.agent_pub_key)],
        "zome_name": zome_name,
        "fn_name": fn_name,
        "cap_secret": cap_secret,
        "payload": msgpack.packb(encode(payload), use_bin_type=True),
        "nonce": nonce if nonce is not None else random_nonce(),
        "expires_at": expires_at if expires_at is not None else nonce_expires_at(),
    }
    data = msgpack.packb(params, use_bin_type=True)
    bytes_hash = hashlib.sha512(data).digest()
    signature = signing_key.sign(bytes_hash)
    return SignedZomeCall(bytes=data, signature=signature)


class CredentialStore:
    """In-memory store of :class:`SigningCredentials`, keyed by cell."""

    def __init__(self):
        self._store: Dict[CellId, SigningCredentials] = {}

    def set(self, cell_id: CellId, credentials: SigningCredentials) -> None:
        self._store[cell_id] = credentials

    def get(self, cell_id: CellId) -> Optional[SigningCredentials]:
        return self._store.get(cell_id)
