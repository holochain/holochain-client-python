"""The admin interface client."""

from __future__ import annotations

from typing import Any, List, Optional

from .._api import ApiClient
from .._transport import DEFAULT_ORIGIN, WebsocketConnection
from ..hash import ActionHash, AgentPubKey, DnaHash
from ..signing import (
    SigningCredentials,
    SigningKeyPair,
    CredentialStore,
    random_cap_secret,
)
from ..types.app import AppInfo, AppInterfaceInfo
from ..types.capability import (
    CapAccessAssigned,
    GrantedFunctions,
    GrantedFunctionsAll,
    GrantZomeCallCapabilityPayload,
    ZomeCallCapGrant,
)
from ..types.cell import CellId
from ..types.common import AppAuthenticationToken, InstalledAppId
from .types import (
    AppAuthenticationTokenIssued,
    AppBundleSource,
    DeleteCloneCellPayload,
    InstallAppPayload,
)


class AdminClient(ApiClient):
    """Client for a conductor admin websocket interface."""

    def __init__(self, connection: WebsocketConnection):
        super().__init__(connection)
        self.credentials = CredentialStore()

    @classmethod
    async def connect(cls, url: str, *, origin: str = DEFAULT_ORIGIN) -> "AdminClient":
        connection = await WebsocketConnection.connect(url, origin=origin)
        return cls(connection)

    # -- DNA / cell introspection ------------------------------------------ #
    async def list_dnas(self) -> List[DnaHash]:
        return await self._send(
            "list_dnas", response_type=List[DnaHash], expect="dnas_listed"
        )

    async def list_cell_ids(self) -> List[CellId]:
        return await self._send(
            "list_cell_ids", response_type=List[CellId], expect="cell_ids_listed"
        )

    async def get_dna_definition(self, cell_id: CellId) -> Any:
        # ``DnaDef`` is returned as a decoded structure (pass-through).
        return await self._send(
            "get_dna_definition", cell_id, expect="dna_definition_returned"
        )

    async def generate_agent_pub_key(self) -> AgentPubKey:
        return await self._send(
            "generate_agent_pub_key",
            response_type=AgentPubKey,
            expect="agent_pub_key_generated",
        )

    # -- App lifecycle ------------------------------------------------------ #
    async def install_app(
        self,
        source: AppBundleSource,
        *,
        agent_key: Optional[AgentPubKey] = None,
        installed_app_id: Optional[InstalledAppId] = None,
        network_seed: Optional[str] = None,
        roles_settings: Optional[Any] = None,
        ignore_genesis_failure: bool = False,
    ) -> AppInfo:
        payload = InstallAppPayload(
            source=source,
            agent_key=agent_key,
            installed_app_id=installed_app_id,
            network_seed=network_seed,
            roles_settings=roles_settings,
            ignore_genesis_failure=ignore_genesis_failure,
        )
        return await self._send(
            "install_app", payload, response_type=AppInfo, expect="app_installed"
        )

    async def uninstall_app(
        self, installed_app_id: InstalledAppId, *, force: bool = False
    ) -> None:
        await self._send(
            "uninstall_app",
            {"installed_app_id": installed_app_id, "force": force},
            expect="app_uninstalled",
        )

    async def enable_app(self, installed_app_id: InstalledAppId) -> AppInfo:
        return await self._send(
            "enable_app",
            {"installed_app_id": installed_app_id},
            response_type=AppInfo,
            expect="app_enabled",
        )

    async def disable_app(self, installed_app_id: InstalledAppId) -> None:
        await self._send(
            "disable_app",
            {"installed_app_id": installed_app_id},
            expect="app_disabled",
        )

    async def list_apps(self, *, status_filter: Optional[str] = None) -> List[AppInfo]:
        return await self._send(
            "list_apps",
            {"status_filter": status_filter},
            response_type=List[AppInfo],
            expect="apps_listed",
        )

    async def delete_clone_cell(self, payload: DeleteCloneCellPayload) -> None:
        await self._send("delete_clone_cell", payload, expect="clone_cell_deleted")

    # -- App interfaces & auth tokens -------------------------------------- #
    async def attach_app_interface(
        self,
        *,
        port: Optional[int] = None,
        allowed_origins: str = "*",
        installed_app_id: Optional[InstalledAppId] = None,
    ) -> int:
        result = await self._send(
            "attach_app_interface",
            {
                "port": port,
                "danger_bind_addr": None,
                "allowed_origins": allowed_origins,
                "installed_app_id": installed_app_id,
            },
            expect="app_interface_attached",
        )
        return result["port"]

    async def list_app_interfaces(self) -> List[AppInterfaceInfo]:
        return await self._send(
            "list_app_interfaces",
            response_type=List[AppInterfaceInfo],
            expect="app_interfaces_listed",
        )

    async def issue_app_authentication_token(
        self,
        installed_app_id: InstalledAppId,
        *,
        expiry_seconds: int = 30,
        single_use: bool = True,
    ) -> AppAuthenticationTokenIssued:
        return await self._send(
            "issue_app_authentication_token",
            {
                "installed_app_id": installed_app_id,
                "expiry_seconds": expiry_seconds,
                "single_use": single_use,
            },
            response_type=AppAuthenticationTokenIssued,
            expect="app_authentication_token_issued",
        )

    async def revoke_app_authentication_token(
        self, token: AppAuthenticationToken
    ) -> None:
        await self._send(
            "revoke_app_authentication_token",
            token,
            expect="app_authentication_token_revoked",
        )

    # -- Agent info -------------------------------------------------------- #
    async def add_agent_info(self, agent_infos: List[str]) -> None:
        await self._send(
            "add_agent_info", {"agent_infos": agent_infos}, expect="agent_info_added"
        )

    async def agent_info(
        self, *, dna_hashes: Optional[List[DnaHash]] = None
    ) -> List[str]:
        return await self._send(
            "agent_info",
            {"dna_hashes": dna_hashes},
            response_type=List[str],
            expect="agent_info",
        )

    # -- Capabilities ------------------------------------------------------ #
    async def grant_zome_call_capability(
        self, payload: GrantZomeCallCapabilityPayload
    ) -> ActionHash:
        return await self._send(
            "grant_zome_call_capability",
            payload,
            response_type=ActionHash,
            expect="zome_call_capability_granted",
        )

    async def revoke_zome_call_capability(
        self, action_hash: ActionHash, cell_id: CellId
    ) -> None:
        await self._send(
            "revoke_zome_call_capability",
            {"action_hash": action_hash, "cell_id": cell_id},
            expect="zome_call_capability_revoked",
        )

    async def list_capability_grants(
        self, installed_app_id: InstalledAppId, *, include_revoked: bool = False
    ) -> Any:
        return await self._send(
            "list_capability_grants",
            {"installed_app_id": installed_app_id, "include_revoked": include_revoked},
            expect="capability_grants_info",
        )

    async def authorize_signing_credentials(
        self,
        cell_id: CellId,
        *,
        functions: Optional[GrantedFunctions] = None,
    ) -> SigningCredentials:
        """Generate a signing keypair, grant it a zome-call capability on
        ``cell_id``, store the resulting credentials, and return them."""
        keypair = SigningKeyPair()
        cap_secret = random_cap_secret()
        grant = GrantZomeCallCapabilityPayload(
            cell_id=cell_id,
            cap_grant=ZomeCallCapGrant(
                tag="zome-call-signing-key",
                access=CapAccessAssigned(
                    secret=cap_secret, assignees=[keypair.agent_pub_key]
                ),
                functions=functions or GrantedFunctionsAll(),
            ),
        )
        await self.grant_zome_call_capability(grant)
        credentials = SigningCredentials(cap_secret=cap_secret, signing_key=keypair)
        self.credentials.set(cell_id, credentials)
        return credentials

    # -- Introspection dumps (pass-through) -------------------------------- #
    async def dump_state(self, cell_id: CellId) -> str:
        return await self._send(
            "dump_state", {"cell_id": cell_id}, expect="state_dumped"
        )

    async def dump_conductor_state(self) -> str:
        return await self._send("dump_conductor_state", expect="conductor_state_dumped")

    async def dump_full_state(
        self, cell_id: CellId, *, dht_ops_cursor: Optional[int] = None
    ) -> Any:
        return await self._send(
            "dump_full_state",
            {"cell_id": cell_id, "dht_ops_cursor": dht_ops_cursor},
            expect="full_state_dumped",
        )

    async def dump_network_metrics(
        self,
        *,
        dna_hash: Optional[DnaHash] = None,
        include_dht_summary: bool = False,
    ) -> Any:
        return await self._send(
            "dump_network_metrics",
            {"dna_hash": dna_hash, "include_dht_summary": include_dht_summary},
            expect="network_metrics_dumped",
        )

    async def dump_network_stats(self) -> Any:
        return await self._send("dump_network_stats", expect="network_stats_dumped")

    async def storage_info(self) -> Any:
        return await self._send("storage_info", expect="storage_info")
