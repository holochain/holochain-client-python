"""Holochain ``HoloHash`` types.

A HoloHash is 39 bytes: a 3-byte multihash type prefix, a 32-byte hash
("core"), and a 4-byte DHT location. They are modelled here as subclasses of
``bytes`` so they serialize transparently as msgpack ``bin`` while still
carrying type information and validation.

The human readable form is multibase base64url (no padding) with a leading
``u``, e.g. ``uhCkk...`` for an :class:`ActionHash`.
"""

from __future__ import annotations

import base64

# 3-byte multihash prefixes, from holo_hash/src/hash_type/primitive.rs
AGENT_PREFIX = bytes([0x84, 0x20, 0x24])
ENTRY_PREFIX = bytes([0x84, 0x21, 0x24])
DHTOP_PREFIX = bytes([0x84, 0x24, 0x24])
WARRANT_PREFIX = bytes([0x84, 0x2C, 0x24])
DNA_PREFIX = bytes([0x84, 0x2D, 0x24])
ACTION_PREFIX = bytes([0x84, 0x29, 0x24])
WASM_PREFIX = bytes([0x84, 0x2A, 0x24])
EXTERNAL_PREFIX = bytes([0x84, 0x2F, 0x24])

HASH_LENGTH = 39
PREFIX_LENGTH = 3
CORE_LENGTH = 32
LOCATION_LENGTH = 4


class HoloHash(bytes):
    """Base class for all 39-byte Holochain hashes.

    Subclasses pin a specific 3-byte ``prefix``. ``HoloHash`` itself accepts any
    valid 39-byte hash regardless of prefix.
    """

    prefix: bytes | None = None

    def __new__(cls, value: bytes):
        if len(value) != HASH_LENGTH:
            raise ValueError(
                f"{cls.__name__} must be {HASH_LENGTH} bytes, got {len(value)}"
            )
        if cls.prefix is not None and bytes(value[:PREFIX_LENGTH]) != cls.prefix:
            raise ValueError(
                f"{cls.__name__} expects prefix {list(cls.prefix)}, "
                f"got {list(value[:PREFIX_LENGTH])}"
            )
        return super().__new__(cls, value)

    @property
    def core(self) -> bytes:
        """The 32-byte hash, without prefix or location."""
        return bytes(self[PREFIX_LENGTH : PREFIX_LENGTH + CORE_LENGTH])

    @property
    def location(self) -> bytes:
        """The 4-byte DHT location suffix."""
        return bytes(self[-LOCATION_LENGTH:])

    def to_b64(self) -> str:
        """Multibase base64url (no padding) form with leading ``u``."""
        return "u" + base64.urlsafe_b64encode(self).decode("ascii").rstrip("=")

    @classmethod
    def from_b64(cls, value: str):
        if value.startswith("u"):
            value = value[1:]
        padding = "=" * (-len(value) % 4)
        return cls(base64.urlsafe_b64decode(value + padding))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.to_b64()})"


class AgentPubKey(HoloHash):
    prefix = AGENT_PREFIX


class EntryHash(HoloHash):
    prefix = ENTRY_PREFIX


class DhtOpHash(HoloHash):
    prefix = DHTOP_PREFIX


class WarrantHash(HoloHash):
    prefix = WARRANT_PREFIX


class DnaHash(HoloHash):
    prefix = DNA_PREFIX


class ActionHash(HoloHash):
    prefix = ACTION_PREFIX


class WasmHash(HoloHash):
    prefix = WASM_PREFIX


class ExternalHash(HoloHash):
    prefix = EXTERNAL_PREFIX


# AnyDhtHash can be an Entry or Action hash; AnyLinkableHash adds External.
AnyDhtHash = HoloHash
AnyLinkableHash = HoloHash

_PREFIX_TO_CLASS = {
    AGENT_PREFIX: AgentPubKey,
    ENTRY_PREFIX: EntryHash,
    DHTOP_PREFIX: DhtOpHash,
    WARRANT_PREFIX: WarrantHash,
    DNA_PREFIX: DnaHash,
    ACTION_PREFIX: ActionHash,
    WASM_PREFIX: WasmHash,
    EXTERNAL_PREFIX: ExternalHash,
}


def hash_from_raw(value: bytes) -> HoloHash:
    """Build the most specific ``HoloHash`` subclass for ``value`` by prefix."""
    cls = _PREFIX_TO_CLASS.get(bytes(value[:PREFIX_LENGTH]), HoloHash)
    return cls(value)
