"""Capability grant types for authorizing zome calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from ..hash import AgentPubKey
from ..serde import TaggedUnion, variant
from .cell import CellId
from .common import CapSecret, FunctionName, ZomeName

GrantedFunction = Tuple[ZomeName, FunctionName]


class GrantedFunctions(TaggedUnion):
    """Which zome functions a capability grants access to."""


@variant(GrantedFunctions, "all")
@dataclass
class GrantedFunctionsAll:
    pass


@variant(GrantedFunctions, "listed")
@dataclass
class GrantedFunctionsListed:
    functions: List[GrantedFunction] = field(metadata={"newtype": True})


class CapAccess(TaggedUnion):
    """Access requirements for a capability grant."""


@variant(CapAccess, "unrestricted")
@dataclass
class CapAccessUnrestricted:
    pass


@variant(CapAccess, "transferable")
@dataclass
class CapAccessTransferable:
    secret: CapSecret


@variant(CapAccess, "assigned")
@dataclass
class CapAccessAssigned:
    secret: CapSecret
    assignees: List[AgentPubKey]


@dataclass
class ZomeCallCapGrant:
    """A capability grant for making zome calls."""

    tag: str
    access: CapAccess
    functions: GrantedFunctions


@dataclass
class GrantZomeCallCapabilityPayload:
    cell_id: CellId
    cap_grant: ZomeCallCapGrant
