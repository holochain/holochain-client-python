"""Cell-related types: ``CellId``, DNA modifiers, and ``CellInfo``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ..hash import AgentPubKey, DnaHash
from ..serde import TaggedUnion, variant
from .common import NetworkSeed

# A clone cell identifier, formatted ``<role_name>.<index>``.
CloneId = str


@dataclass(frozen=True)
class CellId:
    """Identifies a cell: a ``(DnaHash, AgentPubKey)`` pair.

    Serializes as a 2-element array, matching Rust's tuple-struct ``CellId``.
    """

    dna_hash: DnaHash
    agent_pub_key: AgentPubKey

    def __to_wire__(self) -> list:
        return [bytes(self.dna_hash), bytes(self.agent_pub_key)]

    @classmethod
    def __from_wire__(cls, data: Any) -> "CellId":
        return cls(DnaHash(data[0]), AgentPubKey(data[1]))


@dataclass
class DnaModifiers:
    """Modifiers that, together with the integrity zomes, define a DNA hash."""

    network_seed: NetworkSeed
    # ``SerializedBytes`` of the DNA properties (msgpack-encoded), or ``None``.
    properties: Optional[bytes] = None


class CellInfo(TaggedUnion):
    """Information about a cell, as returned in ``AppInfo``."""


@variant(CellInfo, "provisioned")
@dataclass
class ProvisionedCell:
    cell_id: CellId
    dna_modifiers: DnaModifiers
    name: str


@variant(CellInfo, "cloned")
@dataclass
class ClonedCell:
    cell_id: CellId
    clone_id: CloneId
    original_dna_hash: DnaHash
    dna_modifiers: DnaModifiers
    name: str
    enabled: bool


@variant(CellInfo, "stem")
@dataclass
class StemCell:
    original_dna_hash: DnaHash
    dna_modifiers: DnaModifiers
    name: Optional[str] = None


def decode_cell_info(data: Any) -> Any:
    return CellInfo.__from_wire__(data)
