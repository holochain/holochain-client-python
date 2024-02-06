from typing import Any, Dict, List, Optional
import asyncio
import websockets
from holochain_client.api.admin.types import AdminRequest, AppInfo, DumpNetworkStats, ListApps, WireMessageRequest
import msgpack
import dataclasses
import re
import json
from holochain_client.api.common.pending_request_pool import PendingRequestPool

class AppClient:
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
    
    async def call_zome(self) -> Any:
        pass
