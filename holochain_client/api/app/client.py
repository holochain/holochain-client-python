from typing import Any, Dict, List, Optional
import asyncio
import websockets
from holochain_client.api.app.types import ZomeCallUnsigned
from holochain_client.api.common.pending_request_pool import PendingRequestPool
from holochain_client.api.common.request import create_wire_message_request
from holochain_client.api.common.signing import get_from_creds_store
import msgpack
from nacl.utils import random
from datetime import datetime

class AppClient:
    client: websockets.WebSocketClientProtocol
    requestId: int = 0
    pendingRequestPool: PendingRequestPool
    defaultTimeout: int

    @classmethod
    async def create(cls, url: str, defaultTimeout: int = 60):
        self = cls()
        self.client = await websockets.connect(url)
        self.pendingRequestPool = PendingRequestPool(self.client)
        self.defaultTimeout = defaultTimeout
        return self

    async def call_zome(self, request: ZomeCallUnsigned) -> bytes:
        """
        :return: The literal response from the zome call
        """
        signing_credentials = get_from_creds_store(request.cell_id)
        if signing_credentials is None:
            raise Exception(
                f"No signing credentials have been authorized for cell_id: {request.cell_id}"
            )

        payload = {
            'cell_id': request.cell_id,
            'zome_name': request.zome_name,
            'fn_name': request.fn_name,
            'payload': msgpack.packb(request.payload),
            'provenance': request.provenance,
            'nonce': random(32),
            'cap_secret': request.cap_secret,
            # 5 minutes in microseconds
            'expires_at': (datetime.now().timestamp() + 5 * 60) * 1e6
        }
        response = await self._exchange(request)
        assert response["type"] == "zome_called", f"response was: {response}"
        return response["data"]

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
