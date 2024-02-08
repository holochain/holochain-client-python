import dataclasses
from typing import Dict, Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from holochain_client.api.admin.client import AdminClient
from holochain_client.api.admin.types import (
    CapAccessAssigned,
    GrantZomeCallCapability,
    GrantedFunctions,
    ZomeCallCapGrant,
)
from holochain_client.api.common.types import AgentPubKey, CellId
import os
import base64


class SigningKeyWithIdentity:
    _signing_key: Ed25519PrivateKey

    """This will be recognised by Holochain as an agent public key but just contains the generated signing key associated with the signing keypair above."""
    identity: AgentPubKey

    def __init__(self, signing_key: Ed25519PrivateKey):
        self._signing_key = signing_key

        # The first 3 bytes are the constant AGENT_PREFIX from holochain/holochain and the last 4 bytes are the location bytes which
        # are deliberately set to [0, 0, 0, 0] since this agent identity is only used for signing and so its location is not relevant.
        self.identity = bytes(
            [
                132,
                32,
                36,
                *signing_key.public_key().public_bytes_raw(),
                0,
                0,
                0,
                0,
            ]
        )
        assert len(self.identity) == 39

    def sign(self, data: bytes) -> bytes:
        return self._signing_key.sign(data)


@dataclasses.dataclass
class SigningCredentials:
    cap_secret: bytes
    signing_key: SigningKeyWithIdentity


def generate_signing_keypair() -> SigningKeyWithIdentity:
    signing_key = Ed25519PrivateKey.generate()

    return SigningKeyWithIdentity(signing_key)


CREDS_STORE: Dict[str, SigningCredentials] = {}


def _add_to_creds_store(cell_id: CellId, creds: SigningCredentials):
    CREDS_STORE[base64.b64encode(bytes([*cell_id[0], *cell_id[1]]))] = creds


def get_from_creds_store(cell_id: CellId) -> Optional[SigningCredentials]:
    return CREDS_STORE.get(base64.b64encode(bytes([*cell_id[0], *cell_id[1]])))


async def authorize_signing_credentials(
    admin_client: AdminClient,
    cell_id: CellId,
    functions: Optional[GrantedFunctions] = None,
):
    signing_keypair = generate_signing_keypair()
    cap_secret = os.urandom(64)
    await admin_client.grant_zome_call_capability(
        GrantZomeCallCapability(
            cell_id=cell_id,
            cap_grant=ZomeCallCapGrant(
                tag="zome-call-signing-key",
                functions=functions if functions else {"All": None},
                access={
                    "Assigned": CapAccessAssigned(
                        secret=cap_secret, assignees=[signing_keypair.identity]
                    )
                },
            ),
        )
    )

    _add_to_creds_store(cell_id, SigningCredentials(cap_secret, signing_keypair))
