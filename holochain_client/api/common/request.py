from typing import Any
from holochain_client.api.admin.types import (
    AdminRequest,
    WireMessageRequest,
)
import msgpack
import dataclasses
import re


def tag_from_type(req: Any) -> str:
    # TODO compile
    return re.sub(r"(?<!^)(?=[A-Z])", "_", req.__class__.__name__).lower()


def _create_request(req: Any, tag: str) -> bytes:
    if isinstance(req, list):
        data = [dataclasses.asdict(x) for x in req]
    elif isinstance(req, bytes):
        data = req
    else:
        data = dataclasses.asdict(req)

    if len(data) == 0:
        # If there is no data, we should send None instead of an empty dict
        data = None
    elif isinstance(data, dict):
        # Remove any None values from the data, no need to send fields without values
        data = {k: v for k, v in data.items() if v is not None}
    req = AdminRequest(tag, data)
    # print("Sending request: ", req)  # TODO logging
    return msgpack.packb(dataclasses.asdict(req))


def create_wire_message_request(req: Any, tag: str, requestId: int) -> bytes:
    data = _create_request(req, tag)
    msg = WireMessageRequest(id=requestId, data=[x for x in data])
    return msgpack.packb(dataclasses.asdict(msg))
