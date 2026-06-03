"""Low-level WebSocket transport for the Holochain conductor API.

Handles the ``holochain_websocket`` wire framing — an outer msgpack map
``{"type": "request"|"response"|"signal"|"authenticate", "id"?, "data": <bin>}``
where ``data`` is the msgpack-encoded inner payload — plus request/response
correlation by id and dispatch of unsolicited signals.
"""

from __future__ import annotations

import asyncio
import itertools
from typing import Any, Callable, Optional

import msgpack
from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed

# Conductor websockets reject connections without an Origin header. The value is
# only meaningful when the interface restricts allowed origins.
DEFAULT_ORIGIN = "holochain-client-python"

SignalHandler = Callable[[bytes], Any]


class ConductorError(Exception):
    """An ``error`` response returned by the conductor."""


class WebsocketClosed(Exception):
    """Raised for in-flight requests when the connection closes."""


def _pack(obj: Any) -> bytes:
    return msgpack.packb(obj, use_bin_type=True)


def _unpack(data: bytes) -> Any:
    return msgpack.unpackb(data, raw=False)


class WebsocketConnection:
    """A single conductor WebSocket connection."""

    def __init__(self, ws, origin: str = DEFAULT_ORIGIN):
        self._ws = ws
        self._origin = origin
        self._ids = itertools.count(1)
        self._pending: dict[int, asyncio.Future] = {}
        self._signal_handlers: list[SignalHandler] = []
        self._reader: Optional[asyncio.Task] = None

    @classmethod
    async def connect(
        cls, url: str, origin: str = DEFAULT_ORIGIN
    ) -> "WebsocketConnection":
        ws = await ws_connect(url, additional_headers={"Origin": origin})
        self = cls(ws, origin)
        self._reader = asyncio.create_task(self._read_loop())
        return self

    def on_signal(self, handler: SignalHandler) -> None:
        self._signal_handlers.append(handler)

    async def authenticate(self, payload: Any) -> None:
        """Send an ``authenticate`` frame (no response is returned)."""
        frame = _pack({"type": "authenticate", "data": _pack(payload)})
        await self._ws.send(frame)

    async def request(self, payload: Any) -> Any:
        """Send a ``request`` frame and await the decoded inner response."""
        req_id = next(self._ids)
        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[req_id] = fut
        frame = _pack({"type": "request", "id": req_id, "data": _pack(payload)})
        try:
            await self._ws.send(frame)
            return await fut
        finally:
            self._pending.pop(req_id, None)

    async def _read_loop(self) -> None:
        try:
            async for raw in self._ws:
                self._dispatch(raw)
        except ConnectionClosed:
            pass
        finally:
            closed = WebsocketClosed("connection closed")
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(closed)
            self._pending.clear()

    def _dispatch(self, raw: bytes) -> None:
        wire = _unpack(raw)
        kind = wire.get("type")
        if kind == "response":
            fut = self._pending.get(wire["id"])
            if fut is None or fut.done():
                return
            data = wire.get("data")
            inner = _unpack(data) if data is not None else None
            fut.set_result(inner)
        elif kind == "signal":
            data = wire.get("data")
            if data is None:
                return
            for handler in self._signal_handlers:
                handler(data)

    async def close(self) -> None:
        if self._reader is not None:
            self._reader.cancel()
        await self._ws.close()
