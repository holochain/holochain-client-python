from typing import Any
from holochain_client.api.admin.types import (
    AdminRequest,
    WireMessageRequest,
)
import msgpack
import dataclasses
import re
from holochain_client.api.common.pending_request_pool import PendingRequestPool
from holochain_client.api.common.types import AgentPubKey


def _create_request(req: Any) -> bytes:
    # TODO compile
    tag = re.sub(r"(?<!^)(?=[A-Z])", "_", req.__class__.__name__).lower()
    data = dataclasses.asdict(req)
    if len(data) == 0:
        # If there is no data, we should send None instead of an empty dict
        data = None
    else:
        # Remove any None values from the data, no need to send fields without values
        data = {k: v for k, v in data.items() if v is not None}
    req = AdminRequest(tag, data)
    print("Sending request: ", req) # TODO logging
    return msgpack.packb(dataclasses.asdict(req))


def create_wire_message_request(req: Any, requestId: int) -> bytes:
    data = _create_request(req)
    msg = WireMessageRequest(id=requestId, data=[x for x in data])
    return msgpack.packb(dataclasses.asdict(msg))
