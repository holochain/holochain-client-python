from typing import Any, Dict, List, Optional
import asyncio
import websockets
from holochain_client.api.admin.types import AdminRequest, AppInfo, DumpNetworkStats, ListApps, WireMessageRequest
import msgpack
import dataclasses
import re
import json
from holochain_client.api.common.pending_request_pool import PendingRequestPool

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

    async def list_apps(self, request: ListApps = ListApps()) -> List[AppInfo]:
        response = await self._exchange(request)
        assert response["type"] == "apps_listed"
        return [AppInfo(**x) for x in response["data"]]

    async def dump_network_stats(self, request: DumpNetworkStats = DumpNetworkStats()) -> object:
        response = await self._exchange(request)
        assert response["type"] == "network_stats_dumped", f"got: {response}"
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
        data = None
    req = AdminRequest(tag, data)
    print("Sending request: ", req)
    return msgpack.packb(dataclasses.asdict(req))

def _create_wire_message_request(req: Any, requestId: int) -> bytes:
    data = _create_admin_request(req)
    msg = WireMessageRequest(id = requestId, data = [x for x in data])
    return msgpack.packb(dataclasses.asdict(msg))
