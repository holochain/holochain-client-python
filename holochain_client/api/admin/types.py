from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from holochain_client.api.common.types import (
    AgentPubKey,
    CellId,
    DnaHash,
    MembraneProof,
    NetworkSeed,
    RoleName,
)


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
    provisioning: Optional[
        Union[CellProvisioningCreate, CellProvisioningCloneOnly]
    ] = None


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


AppStatusFilter = Enum(
    "AppStatusFilter", ["Enabled", "Disabled", "Running", "Stopped", "Paused"]
)


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


@dataclass
class CellInfoCloned:
    cell_id: CellId
    clone_id: str
    original_dna_hash: DnaHash
    dna_modifiers: DnaModifiers
    name: str
    enabled: bool


@dataclass
class CellInfoStem:
    original_dna_hash: DnaHash
    dna_modifiers: DnaModifiers
    name: Optional[str]


@dataclass
class AppinfoStatusPaused:
    reason: Any  # TODO
    type: str = "Paused"


@dataclass
class AppInfoStatusDisabled:
    reason: Any  # TODO
    type: str = "Disabled"


@dataclass
class AppinfoStatusRunning:
    type: str = "Running"


CellInfoKind = Enum("CellInfoKind", ["provisioned", "cloned", "stem"])


@dataclass
class AppInfo:
    installed_app_id: str
    cell_info: Dict[
        RoleName,
        List[
            Dict[CellInfoKind, Union[CellInfoProvisioned, CellInfoCloned, CellInfoStem]]
        ],
    ]
    status: Union[AppinfoStatusPaused, AppInfoStatusDisabled, AppinfoStatusRunning]
    agent_pub_key: AgentPubKey
    manifest: AppManifest


@dataclass
class CapAccessUnrestricted:
    type: str = "Unrestricted"


@dataclass
class CapAccessTransferable:
    secret: bytes
    type: str = "Transferable"


@dataclass
class CapAccessAssigned:
    secret: bytes
    assignees: List[AgentPubKey]


GrantedFunctionKind = Enum("GrantedFunctionKind", ["All", "Listed"])
GrantedFunctions = Dict[GrantedFunctionKind, Union[None, List[str]]]

CapAccessKind = Enum("CapAccessKind", ["Unrestricted", "Transferable", "Assigned"])


@dataclass
class ZomeCallCapGrant:
    tag: str
    access: Dict[
        CapAccessAssigned,
        Union[CapAccessUnrestricted, CapAccessTransferable, CapAccessAssigned],
    ]
    functions: GrantedFunctions


@dataclass
class GrantZomeCallCapability:
    cell_id: CellId
    cap_grant: ZomeCallCapGrant


@dataclass
class EnableApp:
    installed_app_id: str


@dataclass
class AppEnabled:
    app: AppInfo
    errors: List[Tuple[CellId, str]]


@dataclass
class AttachAppInterface:
    port: Optional[int] = None


@dataclass
class AppInterfaceAttached:
    port: int


@dataclass
class ListAppInterfaces:
    pass


@dataclass
class InterfaceDriverWebsocket:
    port: int
    type: str = "websocket"


@dataclass
class AddAdminInterface:
    driver: Union[InterfaceDriverWebsocket]


@dataclass
class RegisterDnaPayloadPath:
    path: str
    modifiers: Optional[DnaModifiers] = None


@dataclass
class RegisterDnaPayloadHash:
    hash: DnaHash
    modifiers: DnaModifiers


RegisterDnaPayload = Union[RegisterDnaPayloadPath, RegisterDnaPayloadHash]


@dataclass
class UninstallApp:
    installed_app_id: str


@dataclass
class ListDnas:
    pass
