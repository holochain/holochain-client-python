"""Application-level types: ``AppInfo``, ``AppStatus``, app interface info."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..hash import AgentPubKey
from ..serde import TaggedUnion, variant
from .cell import CellInfo
from .common import InstalledAppId, RoleName, Timestamp


def _newtype(typ):
    """Field for a single-payload (newtype) enum variant."""
    return field(metadata={"newtype": True})


class DisabledAppReason(TaggedUnion):
    """Why an app is disabled."""


@variant(DisabledAppReason, "never_started")
@dataclass
class NeverStarted:
    pass


@variant(DisabledAppReason, "not_started_after_providing_memproofs")
@dataclass
class NotStartedAfterProvidingMemproofs:
    pass


@variant(DisabledAppReason, "user")
@dataclass
class DisabledByUser:
    pass


@variant(DisabledAppReason, "error")
@dataclass
class DisabledByError:
    message: str = _newtype(str)


class AppStatus(TaggedUnion):
    """An app's lifecycle status."""


@variant(AppStatus, "enabled")
@dataclass
class AppEnabled:
    pass


@variant(AppStatus, "disabled")
@dataclass
class AppDisabled:
    reason: DisabledAppReason = _newtype(DisabledAppReason)


@variant(AppStatus, "awaiting_memproofs")
@dataclass
class AppAwaitingMemproofs:
    pass


@dataclass
class AppInfo:
    """Information about an installed app."""

    installed_app_id: InstalledAppId
    cell_info: Dict[RoleName, List[CellInfo]]
    status: AppStatus
    agent_pub_key: AgentPubKey
    # The original ``AppManifest`` is left as a decoded structure (pass-through).
    manifest: Any
    installed_at: Timestamp


@dataclass
class AppInterfaceInfo:
    """An attached app interface, as listed by ``list_app_interfaces``."""

    port: int
    allowed_origins: Any
    installed_app_id: Optional[InstalledAppId] = None
