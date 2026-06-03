"""Types specific to the app interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..types.cell import CellId
from ..types.common import ZomeName


@dataclass
class AppSignal:
    """An application signal emitted by a cell via ``emit_signal``."""

    cell_id: CellId
    zome_name: ZomeName
    # The emitted payload, MessagePack-decoded.
    payload: Any


@dataclass
class SystemSignal:
    """A system-emitted signal."""

    value: Any
