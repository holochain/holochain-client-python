from typing import Dict, Optional
from nacl.signing import SigningKey
from holochain_client.api.admin.client import AdminClient
from holochain_client.api.admin.types import CapAccessAssigned, GrantZomeCallCapability, GrantedFunctions, ZomeCallCapGrant
from holochain_client.api.common.types import AgentPubKey, CellId
from nacl.utils import random
import base64

class SigningKeyWithIdentity:
    _signing_key: SigningKey

    """This will be recognised by Holochain as an agent public key but just contains the generated signing key associated with the signing keypair above."""
    identity: AgentPubKey

    def __init__(self, signing_key: SigningKey):
        self._signing_key = signing_key

        # The first 3 bytes are the constant AGENT_PREFIX from holochain/holochain and the last 4 bytes are the location bytes which
        # are deliberately set to [0, 0, 0, 0] since this agent identity is only used for signing and so its location is not relevant.
        self.identity = bytes([132, 32, 36, *bytes(signing_key.verify_key.to_curve25519_public_key()), 0, 0, 0, 0])
        assert len(self.identity) == 39


class SigningCredentials:
    cap_secret: bytes
    signing_key: SigningKeyWithIdentity


def generate_signing_keypair() -> SigningKeyWithIdentity:
    signing_key = SigningKey.generate()

    return SigningKeyWithIdentity(signing_key)


CREDS_STORE: Dict[str, SigningCredentials] = {}

def _add_to_creds_store(cell_id: CellId, creds: SigningCredentials):
    CREDS_STORE[base64.b64encode(bytes([*cell_id[0], *cell_id[1]]))] = creds

def _get_from_creds_store(cell_id: CellId) -> Optional[SigningCredentials]:
    return CREDS_STORE.get(base64.b64encode(bytes([*cell_id[0], *cell_id[1]])))

async def authorize_signing_credentials(admin_client: AdminClient, cell_id: CellId, functions: Optional[GrantedFunctions] = None):
    signing_keypair = generate_signing_keypair()
    cap_secret = random(64)
    print("Using cell id ", cell_id)
    print("Using identity ", signing_keypair.identity)
    await admin_client.grant_zome_call_capability(GrantZomeCallCapability(
        cell_id=cell_id,
        cap_grant=ZomeCallCapGrant(
            tag="zome-call-signing-key",
            functions=functions if functions else {"All": None},
            access={"Assigned": CapAccessAssigned(
                secret=cap_secret,
                assignees=[signing_keypair.identity]
            )}
        )
    ))

    _add_to_creds_store(cell_id, SigningCredentials)


