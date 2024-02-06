
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from holochain_client.api.common.types import AgentPubKey, CellId, DnaHash, MembraneProof, NetworkSeed, RoleName

@dataclass
class WireMessageRequest:
    id: int
    data: List[int]
    type: str = "request"

@dataclass
class AdminRequest:
    type: str
    data: Dict

@dataclass
class CellProvisioningCreate:
    deferred: bool
    strategy: str = "Create"

@dataclass
class CellProvisioningCloneOnly:
    strategy: str = "CloneOnly"

@dataclass
class Duration:
    secs: int
    nanos: int

@dataclass
class DnaModifiers:
    network_seed: Optional[NetworkSeed] = None
    properties: Optional[Dict] = None
    origin_time: Optional[int] = None
    quantum_time: Optional[Duration] = None

@dataclass
class AppRoleDnaManifest:
    bundled: str
    modifiers: Dict
    installed_hash: Optional[str] = None
    clone_limit: int = 0


@dataclass
class AppRoleManifest:
    name: RoleName
    dna: AppRoleDnaManifest
    provisioning: Optional[Union[CellProvisioningCreate, CellProvisioningCloneOnly]] = None

@dataclass
class AppManifest:
    manifest_version: str
    name: str
    description: Optional[str]
    roles: List[AppRoleManifest]

@dataclass
class AppBundleSourceBundle:
    manifest: AppManifest
    resources: Dict[str, bytes]

@dataclass
class InstallApp:
    agent_key: AgentPubKey

    # Exactly one of these must be set
    bundle: Optional[AppBundleSourceBundle] = None
    path: Optional[str] = None

    installed_app_id: Optional[str] = None
    membrane_proofs: Dict[RoleName, MembraneProof] = field(default_factory=dict)
    network_seed: Optional[NetworkSeed] = None


@dataclass
class GenerateAgentPubKey:
    pass

AppStatusFilter = Enum("AppStatusFilter", ["Enabled", "Disabled", "Running", "Stopped", "Paused"])

@dataclass
class ListApps:
    status_filter: Optional[AppStatusFilter] = None

@dataclass
class DumpNetworkStats:
    pass

@dataclass
class CellInfoProvisioned:
    cell_id: CellId
    dna_modifiers: DnaModifiers
    name: str
    type: str = "Provisioned"

@dataclass
class CellInfoCloned:
    cell_id: CellId
    clone_id: str
    original_dna_hash: DnaHash
    dna_modifiers: DnaModifiers
    name: str
    enabled: bool
    type: str = "Cloned"

@dataclass
class CellInfoStem:
    original_dna_hash: DnaHash
    dna_modifiers: DnaModifiers
    name: Optional[str]
    type: str = "stem"

@dataclass
class AppinfoStatusPaused:
    reason: Any # TODO
    type: str = "Paused"

@dataclass
class AppInfoStatusDisabled:
    reason: Any # TODO
    type: str = "Disabled"

@dataclass
class AppinfoStatusRunning:
    type: str = "Running"

@dataclass
class AppInfo:
    installed_app_id: str
    cell_info: Dict[RoleName, List[Union[CellInfoProvisioned, CellInfoCloned, CellInfoStem]]]
    status: Union[AppinfoStatusPaused, AppInfoStatusDisabled, AppinfoStatusRunning]
    agent_pub_key: AgentPubKey
    manifest: AppManifest
