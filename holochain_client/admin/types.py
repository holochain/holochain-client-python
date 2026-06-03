"""Request/response payload types specific to the admin interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..hash import AgentPubKey, DnaHash
from ..serde import TaggedUnion, variant
from ..types.cell import CloneId
from ..types.common import (
    AppAuthenticationToken,
    InstalledAppId,
    NetworkSeed,
    Timestamp,
)


class AppBundleSource(TaggedUnion):
    """Where to find an app bundle when installing."""


@variant(AppBundleSource, "bytes")
@dataclass
class AppBundleBytes:
    """Raw ``.happ`` bundle bytes."""

    bundle: bytes = field(metadata={"newtype": True})


@variant(AppBundleSource, "path")
@dataclass
class AppBundlePath:
    """A filesystem path to a ``.happ`` bundle, read by the conductor."""

    path: str = field(metadata={"newtype": True})


@dataclass
class DnaModifiersOpt:
    """Optional DNA modifier overrides."""

    network_seed: Optional[NetworkSeed] = None
    properties: Optional[Any] = None


@dataclass
class InstallAppPayload:
    source: AppBundleSource
    agent_key: Optional[AgentPubKey] = None
    installed_app_id: Optional[InstalledAppId] = None
    network_seed: Optional[NetworkSeed] = None
    roles_settings: Optional[Any] = None
    ignore_genesis_failure: bool = False

    def __to_wire__(self) -> dict:
        # ``source`` is a tagged union; everything else is plain. Optional fields
        # are sent as nil, which the conductor's serde accepts.
        from ..serde import encode

        return {
            "source": encode(self.source),
            "agent_key": encode(self.agent_key),
            "installed_app_id": self.installed_app_id,
            "network_seed": self.network_seed,
            "roles_settings": encode(self.roles_settings),
            "ignore_genesis_failure": self.ignore_genesis_failure,
        }


class CloneCellId(TaggedUnion):
    """Identifies a clone cell, by clone id or by DNA hash."""


@variant(CloneCellId, "clone_id")
@dataclass
class CloneCellByCloneId:
    clone_id: CloneId = field(metadata={"newtype": True})


@variant(CloneCellId, "dna_hash")
@dataclass
class CloneCellByDnaHash:
    dna_hash: DnaHash = field(metadata={"newtype": True})


@dataclass
class DeleteCloneCellPayload:
    app_id: InstalledAppId
    clone_cell_id: CloneCellId


@dataclass
class AppAuthenticationTokenIssued:
    token: AppAuthenticationToken
    expires_at: Optional[Timestamp] = None
