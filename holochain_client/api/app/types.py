import dataclasses
from typing import Optional

from holochain_client.api.common.types import (
    AgentPubKey,
    CellId,
    FunctionName,
    ZomeName,
)


@dataclasses.dataclass
class ZomeCall:
    cell_id: CellId
    zome_name: ZomeName
    fn_name: FunctionName
    payload: bytes
    provenance: AgentPubKey
    signature: bytes
    nonce: bytes
    """Microseconds from unix epoch"""
    expires_at: int
    cap_secret: Optional[bytes] = None
