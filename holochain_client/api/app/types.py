import dataclasses
from typing import Any, Optional

from holochain_client.api.common.types import (
    AgentPubKey,
    CellId,
    FunctionName,
    ZomeName,
)

@dataclasses.dataclass
class ZomeCallUnsigned:
    cell_id: CellId
    zome_name: ZomeName
    fn_name: FunctionName
    payload: Any

@dataclasses.dataclass
class CallZome:
    cell_id: CellId
    zome_name: ZomeName
    fn_name: FunctionName
    payload: bytes
    provenance: AgentPubKey
    signature: bytes
    nonce: bytes
    """Microseconds from unix epoch"""
    expires_at: int
    cap_secret: bytes
