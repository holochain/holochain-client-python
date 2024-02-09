from typing import Any, List
import asyncio
import websockets
from holochain_client.api.admin.types import (
    AppEnabled,
    AppInfo,
    AppInterfaceAttached,
    AttachAppInterface,
    DumpNetworkStats,
    EnableApp,
    GenerateAgentPubKey,
    GrantZomeCallCapability,
    InstallApp,
    ListAppInterfaces,
    ListApps,
)
import json
from holochain_client.api.common.pending_request_pool import PendingRequestPool
from holochain_client.api.common.request import create_wire_message_request
from holochain_client.api.common.types import AgentPubKey


class AdminClient:
    url: str
    defaultTimeout: int

    client: websockets.WebSocketClientProtocol
    requestId: int = 0
    pendingRequestPool: PendingRequestPool

    def __init__(self, url: str, defaultTimeout: int = 60):
        self.url = url
        self.defaultTimeout = defaultTimeout
    
    @classmethod
    async def create(cls, url: str, defaultTimeout: int = 60):
        """The recommended way to create an AdminClient"""
        self = cls(url, defaultTimeout)
        await self.connect()
        return self
    
    def connect_sync(self, event_loop):
        return event_loop.run_until_complete(self.connect())

    async def connect(self):
        self.client = await websockets.connect(self.url)
        self.pendingRequestPool = PendingRequestPool(self.client)

    async def install_app(self, request: InstallApp) -> AppInfo:
        response = await self._exchange(request)
        assert response["type"] == "app_installed", f"response was: {response}"
        return AppInfo(**response["data"])

    async def generate_agent_pub_key(
        self, request: GenerateAgentPubKey = GenerateAgentPubKey()
    ) -> AgentPubKey:
        response = await self._exchange(request)
        assert (
            response["type"] == "agent_pub_key_generated"
        ), f"response was: {response}"
        return response["data"]

    async def list_apps(self, request: ListApps = ListApps()) -> List[AppInfo]:
        response = await self._exchange(request)
        assert response["type"] == "apps_listed", f"response was: {response}"
        return [AppInfo(**x) for x in response["data"]]

    async def enable_app(self, request: EnableApp) -> AppEnabled:
        response = await self._exchange(request)
        assert response["type"] == "app_enabled", f"response was: {response}"
        return AppEnabled(*response["data"])

    async def attach_app_interface(
        self, request: AttachAppInterface = AttachAppInterface()
    ) -> AppInterfaceAttached:
        response = await self._exchange(request)
        assert response["type"] == "app_interface_attached", f"response was: {response}"
        return AppInterfaceAttached(port=int(response["data"]["port"]))

    async def list_app_interfaces(self, request: ListAppInterfaces = ListAppInterfaces()) -> List[int]:
        response = await self._exchange(request)
        assert response["type"] == "app_interfaces_listed", f"response was: {response}"
        return response["data"]

    async def dump_network_stats(
        self, request: DumpNetworkStats = DumpNetworkStats()
    ) -> object:
        response = await self._exchange(request)
        assert response["type"] == "network_stats_dumped", f"response was: {response}"
        return json.loads(response["data"])

    async def grant_zome_call_capability(
        self, grant_zome_call_capability: GrantZomeCallCapability
    ):
        response = await self._exchange(grant_zome_call_capability)
        assert (
            response["type"] == "zome_call_capability_granted"
        ), f"response was: {response}"

    async def close(self):
        await self.client.close()

    async def _exchange(self, request: Any) -> Any:
        requestId = self.requestId
        self.requestId += 1
        req = create_wire_message_request(request, requestId)
        await self.client.send(req)

        completed = asyncio.Event()
        self.pendingRequestPool.add(requestId, completed)
        await asyncio.wait_for(completed.wait(), self.defaultTimeout)

        return self.pendingRequestPool.take_response(requestId)
