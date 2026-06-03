"""Shared request/response envelope handling for the admin and app clients."""

from __future__ import annotations

from typing import Any, Optional

from ._transport import ConductorError, WebsocketConnection
from .serde import decode, encode


class ApiClient:
    """Wraps a :class:`WebsocketConnection` with the conductor's request and
    response envelope (``{"type": <variant>, "value": <content>}``) and turns
    ``error`` responses into :class:`ConductorError`."""

    def __init__(self, connection: WebsocketConnection):
        self._connection = connection

    async def _send(
        self,
        request_type: str,
        value: Any = None,
        *,
        response_type: Any = None,
        expect: Optional[str] = None,
    ) -> Any:
        request: dict[str, Any] = {"type": request_type}
        if value is not None:
            request["value"] = encode(value)
        response = await self._connection.request(request)

        kind = response.get("type")
        content = response.get("value")
        if kind == "error":
            raise _to_error(content)
        if expect is not None and kind != expect:
            raise ConductorError(
                f"unexpected response {kind!r} to {request_type!r}: {content!r}"
            )
        return decode(content, response_type)

    async def close(self) -> None:
        await self._connection.close()


def _to_error(content: Any) -> ConductorError:
    """Turn an ``ExternalApiWireError`` payload into an exception."""
    if isinstance(content, dict) and "type" in content:
        kind = content["type"]
        message = content.get("value")
        return ConductorError(f"{kind}: {message}")
    return ConductorError(str(content))
