"""The app interface client."""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Union

import msgpack

from .._api import ApiClient
from .._transport import ConductorError, DEFAULT_ORIGIN, WebsocketConnection
from ..signing import CredentialStore, SigningCredentials, sign_zome_call
from ..types.app import AppInfo
from ..types.cell import CellId
from ..types.common import AppAuthenticationToken, FunctionName, ZomeName
from .types import AppSignal, SystemSignal

SignalCallback = Callable[[Union[AppSignal, SystemSignal]], Any]


class AppClient(ApiClient):
    """Client for a conductor app websocket interface.

    An app websocket must be authenticated with a token issued by the admin
    interface (:meth:`AdminClient.issue_app_authentication_token`) before any
    request will be answered.
    """

    def __init__(self, connection: WebsocketConnection):
        super().__init__(connection)
        self.credentials = CredentialStore()
        self._signal_callbacks: List[SignalCallback] = []
        connection.on_signal(self._handle_signal)

    @classmethod
    async def connect(
        cls,
        url: str,
        token: AppAuthenticationToken,
        *,
        origin: str = DEFAULT_ORIGIN,
    ) -> "AppClient":
        connection = await WebsocketConnection.connect(url, origin=origin)
        client = cls(connection)
        await connection.authenticate({"token": token})
        return client

    # -- Signals ----------------------------------------------------------- #
    def on_signal(self, callback: SignalCallback) -> None:
        self._signal_callbacks.append(callback)

    def _handle_signal(self, data: bytes) -> None:
        signal = msgpack.unpackb(data, raw=False)
        kind = signal.get("type")
        value = signal.get("value")
        if kind == "app":
            decoded = AppSignal(
                cell_id=CellId.__from_wire__(value["cell_id"]),
                zome_name=value["zome_name"],
                payload=msgpack.unpackb(value["signal"], raw=False),
            )
        elif kind == "system":
            decoded = SystemSignal(value=value)
        else:
            return
        for callback in self._signal_callbacks:
            callback(decoded)

    # -- App info ---------------------------------------------------------- #
    async def app_info(self) -> Optional[AppInfo]:
        return await self._send(
            "app_info", response_type=Optional[AppInfo], expect="app_info"
        )

    # -- Zome calls -------------------------------------------------------- #
    async def call_zome(
        self,
        cell_id: CellId,
        zome_name: ZomeName,
        fn_name: FunctionName,
        payload: Any = None,
        *,
        credentials: Optional[SigningCredentials] = None,
    ) -> Any:
        """Sign and make a zome call, returning the MessagePack-decoded result."""
        credentials = credentials or self.credentials.get(cell_id)
        if credentials is None:
            raise ConductorError(
                f"no signing credentials authorized for cell {cell_id!r}"
            )
        signed = sign_zome_call(
            cell_id=cell_id,
            zome_name=zome_name,
            fn_name=fn_name,
            payload=payload,
            provenance=credentials.signing_key.agent_pub_key,
            signing_key=credentials.signing_key,
            cap_secret=credentials.cap_secret,
        )
        result = await self._send(
            "call_zome",
            {"bytes": signed.bytes, "signature": signed.signature},
            expect="zome_called",
        )
        # The result is the zome's return value as MessagePack bytes.
        return msgpack.unpackb(result, raw=False)

    # -- Network introspection (pass-through) ------------------------------ #
    async def dump_network_metrics(
        self,
        *,
        dna_hash: Optional[Any] = None,
        include_dht_summary: bool = False,
    ) -> Any:
        return await self._send(
            "dump_network_metrics",
            {"dna_hash": dna_hash, "include_dht_summary": include_dht_summary},
            expect="network_metrics_dumped",
        )

    async def dump_network_stats(self) -> Any:
        return await self._send("dump_network_stats", expect="network_stats_dumped")

    async def list_wasm_host_functions(self) -> List[str]:
        return await self._send(
            "list_wasm_host_functions",
            response_type=List[str],
            expect="list_wasm_host_functions",
        )
