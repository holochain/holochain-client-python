from typing import Any, Dict, List, Optional
import asyncio
import websockets
from holochain_client.api.admin.types import AdminRequest, AppInfo, DumpNetworkStats, ListApps, WireMessageRequest
import msgpack
import dataclasses
import re
import json

@dataclasses.dataclass
class PendingRequest:
    id: int
    trigger: asyncio.Event


class PendingRequestPool:
    _requests: Dict[int, PendingRequest] = {}
    _responses: Dict[int, Any] = {}

    def __init__(self, client: websockets.WebSocketClientProtocol):
        asyncio.create_task(self._handle_responses(client))

    def add(self, id: int, trigger: asyncio.Event):
        self._requests[id] = PendingRequest(id, trigger)

    async def _handle_responses(self, client: websockets.WebSocketClientProtocol):
        async for message in client:
            data = msgpack.unpackb(message)
            if "id" in data and "type" in data and data["type"] == "response":
                id = data["id"]
                if id in self._requests:
                    data["data"] = msgpack.unpackb(data["data"])
                    self._responses[id] = data
                    self._requests[id].trigger.set()
                    del self._requests[id]
                else:
                    # TODO logging
                    print(f"Received response for unknown request id: {id}")
    
    def take_response(self, id: int) -> Any:
        return self._responses.pop(id)["data"]
