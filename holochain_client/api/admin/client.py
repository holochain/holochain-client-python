from typing import Any, Dict, List, Optional
import asyncio
import websockets
from holochain_client.api.admin.types import AdminRequest, AppInfo, DumpNetworkStats, GenerateAgentPubKey, InstallApp, ListApps, WireMessageRequest
import msgpack
import dataclasses
import re
import json
from holochain_client.api.common.pending_request_pool import PendingRequestPool
from holochain_client.api.common.types import AgentPubKey

class AdminClient:
    client: websockets.WebSocketClientProtocol
    requestId: int = 0
    pendingRequestPool: PendingRequestPool
    defaultTimeout: Optional[int]

    @classmethod
    async def create(cls, url: str, defaultTimeout: Optional[int] = None):
        self = cls()
        self.client = await websockets.connect(url)
        self.pendingRequestPool = PendingRequestPool(self.client)
        self.defaultTimeout = defaultTimeout
        return self

    async def install_app(self, request: InstallApp) -> AppInfo:
        response = await self._exchange(request)
        assert response["type"] == "app_installed", f"response was: {response}"
        return AppInfo(**response["data"])

    async def generate_agent_pub_key(self, request: GenerateAgentPubKey = GenerateAgentPubKey()) -> AgentPubKey:
        response = await self._exchange(request)
        assert response["type"] == "agent_pub_key_generated", f"response was: {response}"
        return response["data"]

    async def list_apps(self, request: ListApps = ListApps()) -> List[AppInfo]:
        response = await self._exchange(request)
        assert response["type"] == "apps_listed", f"response was: {response}"
        return [AppInfo(**x) for x in response["data"]]

    async def dump_network_stats(self, request: DumpNetworkStats = DumpNetworkStats()) -> object:
        response = await self._exchange(request)
        assert response["type"] == "network_stats_dumped", f"response was: {response}"
        return json.loads(response["data"])

    async def close(self):
        await self.client.close()

    async def _exchange(self, request: Any) -> Any:
        requestId = self.requestId
        self.requestId += 1
        req = _create_wire_message_request(request, requestId)
        await self.client.send(req)

        completed = asyncio.Event()
        self.pendingRequestPool.add(requestId, completed)
        await asyncio.wait_for(completed.wait(), self.defaultTimeout)

        return self.pendingRequestPool.take_response(requestId)


def _create_admin_request(dc: Any) -> bytes:
    # TODO compile
    tag = re.sub(r'(?<!^)(?=[A-Z])', '_', dc.__class__.__name__).lower()
    data = dataclasses.asdict(dc)
    if len(data) == 0:
        # If there is no data, we should send None instead of an empty dict
        data = None
    else:
        # Remove any None values from the data, no need to send fields without values
        data = {k: v for k, v in data.items() if v is not None}
    req = AdminRequest(tag, data)
    print("Sending request: ", req)
    return msgpack.packb(dataclasses.asdict(req))

def _create_wire_message_request(req: Any, requestId: int) -> bytes:
    data = _create_admin_request(req)
    msg = WireMessageRequest(id = requestId, data = [x for x in data])
    return msgpack.packb(dataclasses.asdict(msg))
