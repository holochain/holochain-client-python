from typing import Any
import asyncio
import websockets
from holochain_client.api.app.types import CallZome, ZomeCallUnsigned
from holochain_client.api.common.pending_request_pool import PendingRequestPool
from holochain_client.api.common.request import (
    create_wire_message_request,
    tag_from_type,
)
from holochain_client.api.common.signing import get_from_creds_store
import os
from datetime import datetime
from holochain_serialization import ZomeCallUnsignedPy, get_data_to_sign


class AppClient:
    url: str
    defaultTimeout: int

    client: websockets.WebSocketClientProtocol
    requestId: int = 0
    pendingRequestPool: PendingRequestPool

    def __init__(self, url: str, defaultTimeout: int = 60) -> None:
        self.url = url
        self.defaultTimeout = defaultTimeout

    @classmethod
    async def create(cls, url: str, defaultTimeout: int = 60):
        """The recommended way to create an AppClient"""
        self = cls(url, defaultTimeout)
        await self.connect()
        return self

    def connect_sync(self, event_loop):
        event_loop.run_until_complete(self.connect())

    async def connect(self):
        self.client = await websockets.connect(self.url)
        self.pendingRequestPool = PendingRequestPool(self.client)
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

        provenance = signing_credentials.signing_key.identity  # Request is actually made on behalf of the siging credentials, not the current agent!
        nonce = os.urandom(32)
        expires_at = int((datetime.now().timestamp() + 5 * 60) * 1e6)
        cap_secret = signing_credentials.cap_secret

        zome_call_py = ZomeCallUnsignedPy(
            provenance,
            request.cell_id[0],
            request.cell_id[1],
            request.zome_name,
            request.fn_name,
            request.payload,
            nonce,
            expires_at,
            cap_secret=cap_secret,
        )
        data_to_sign = bytes(get_data_to_sign(zome_call_py))
        signature = signing_credentials.signing_key.sign(data_to_sign)

        request = CallZome(
            cell_id=request.cell_id,
            zome_name=request.zome_name,
            fn_name=request.fn_name,
            payload=request.payload,
            provenance=provenance,
            signature=signature,
            nonce=nonce,
            expires_at=expires_at,
            cap_secret=cap_secret,
        )

        response = await self._exchange(request, tag_from_type(request))
        assert response["type"] == "zome_called", f"response was: {response}"
        return response["data"]

    async def close(self):
        await self.client.close()

    async def _exchange(self, request: Any, tag: str) -> Any:
        requestId = self.requestId
        self.requestId += 1
        req = create_wire_message_request(request, tag, requestId)
        await self.client.send(req)

        completed = asyncio.Event()
        self.pendingRequestPool.add(requestId, completed)
        await asyncio.wait_for(completed.wait(), self.defaultTimeout)

        return self.pendingRequestPool.take_response(requestId)
