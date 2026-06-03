"""Type-driven (de)serialization between Python models and Holochain's wire format.

Holochain serializes with MessagePack via ``serde``. The conventions we mirror:

* structs become maps keyed by ``snake_case`` field names;
* enums are *adjacently tagged* as ``{"type": <variant>, "value": <content>}``
  (the ``value`` key is absent for unit variants);
* byte sequences (including ``HoloHash``) are msgpack ``bin``;
* ``Option<T>`` is either the encoded ``T`` or ``nil``.

Encoding (:func:`encode`) walks a Python object and produces msgpack-ready
primitives. Decoding (:func:`decode`) is *target-typed*: the caller supplies the
expected type, so we never have to guess a structure from its shape — the
failure mode that made the previous client unreliable.
"""

from __future__ import annotations

import dataclasses
import enum
import typing
from typing import Any, Union, get_args, get_origin

from .hash import HoloHash

NoneType = type(None)


# --------------------------------------------------------------------------- #
# Protocol hooks
# --------------------------------------------------------------------------- #
# A type may implement custom wire behaviour with:
#   * instance method ``__to_wire__(self) -> Any``
#   * classmethod ``__from_wire__(cls, data: Any) -> instance``
# These take precedence over the generic dataclass handling below.


def encode(obj: Any) -> Any:
    """Convert ``obj`` into msgpack-ready primitives."""
    if obj is None:
        return None
    if isinstance(obj, HoloHash):
        return bytes(obj)
    if isinstance(obj, (bytes, bytearray)):
        return bytes(obj)
    if isinstance(obj, bool) or isinstance(obj, (int, float, str)):
        return obj
    if hasattr(obj, "__to_wire__"):
        return obj.__to_wire__()
    if isinstance(obj, enum.Enum):
        # Plain C-like enums serialize as their snake_case name.
        return obj.value if isinstance(obj.value, str) else obj.name
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        out: dict[str, Any] = {}
        for f in dataclasses.fields(obj):
            if f.metadata.get("skip"):
                continue
            wire_name = f.metadata.get("rename", f.name)
            value = getattr(obj, f.name)
            if value is None and f.metadata.get("omit_none"):
                continue
            out[wire_name] = encode(value)
        return out
    if isinstance(obj, dict):
        return {k: encode(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [encode(v) for v in obj]
    raise TypeError(f"Cannot encode object of type {type(obj)!r}")


def decode(data: Any, typ: Any) -> Any:
    """Decode msgpack-decoded ``data`` into the expected ``typ``."""
    if typ is None or typ is Any or typ is NoneType:
        return data

    # Custom hook.
    from_wire = getattr(typ, "__from_wire__", None)
    if from_wire is not None and isinstance(typ, type):
        return from_wire(data)

    origin = get_origin(typ)

    # Optional / Union.
    if origin is Union:
        args = [a for a in get_args(typ) if a is not NoneType]
        if data is None:
            return None
        if len(args) == 1:
            return decode(data, args[0])
        # Best-effort for genuine unions: try each until one fits.
        for arg in args:
            try:
                return decode(data, arg)
            except Exception:
                continue
        return data

    if origin in (list, typing.List):
        (item_t,) = get_args(typ) or (Any,)
        return [decode(v, item_t) for v in data]

    if origin in (tuple, typing.Tuple):
        args = get_args(typ)
        if not args:
            return tuple(data)
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(decode(v, args[0]) for v in data)
        return tuple(decode(v, t) for v, t in zip(data, args))

    if origin in (dict, typing.Dict):
        args = get_args(typ) or (Any, Any)
        kt, vt = args
        return {decode(k, kt): decode(v, vt) for k, v in data.items()}

    if isinstance(typ, type) and issubclass(typ, HoloHash):
        if typ is HoloHash:
            # A generic hash (e.g. AnyLinkableHash): resolve by its prefix.
            from .hash import hash_from_raw

            return hash_from_raw(data)
        return typ(data)

    if isinstance(typ, type) and issubclass(typ, enum.Enum):
        try:
            return typ(data)
        except ValueError:
            return typ[data]

    if isinstance(typ, type) and dataclasses.is_dataclass(typ):
        return _decode_dataclass(data, typ)

    # Primitives and anything we don't specialise.
    return data


def _decode_dataclass(data: Any, typ: type) -> Any:
    hints = typing.get_type_hints(typ)
    kwargs: dict[str, Any] = {}
    for f in dataclasses.fields(typ):
        wire_name = f.metadata.get("rename", f.name)
        if isinstance(data, dict) and wire_name in data:
            kwargs[f.name] = decode(data[wire_name], hints.get(f.name, Any))
        elif f.default is not dataclasses.MISSING:
            kwargs[f.name] = f.default
        elif f.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
            kwargs[f.name] = f.default_factory()
        else:
            kwargs[f.name] = None
    return typ(**kwargs)


# --------------------------------------------------------------------------- #
# Adjacently-tagged unions (Rust enums)
# --------------------------------------------------------------------------- #
def variant(union: type, tag: str):
    """Register a dataclass as a ``tag`` variant of an adjacently-tagged union.

    Usage::

        class CellInfo(TaggedUnion): ...

        @variant(CellInfo, "provisioned")
        @dataclass
        class ProvisionedCell: ...
    """

    def register(cls):
        union._variants[tag] = cls  # type: ignore[attr-defined]
        cls._tag = tag
        cls._union = union
        cls.__to_wire__ = to_tagged
        return cls

    return register


class TaggedUnion:
    """Base for Rust enums that carry a variant tag.

    Subclass it to declare a union, then attach variant dataclasses with
    :func:`variant`. Three ``serde`` tagging styles are supported via class
    attributes on the subclass:

    * ``"adjacent"`` (default) — ``{tag_key: <variant>, content_key: <content>}``,
      e.g. ``#[serde(tag = "type", content = "value")]``. Unit variants omit the
      content key.
    * ``"internal"`` — ``{tag_key: <variant>, ...fields}``: the variant's struct
      fields are flattened alongside the tag, e.g. ``#[serde(tag = "type")]`` as
      used by ``Action``.
    * ``"external"`` — a bare string for unit variants, or ``{<variant>: content}``
      for data-carrying variants (serde's default), as used by ``RecordEntry``.

    ``tag_key``/``content_key`` default to ``"type"``/``"value"`` and can be
    overridden (``Entry`` uses ``"entry_type"``/``"entry"``).
    """

    _variants: dict[str, type] = {}
    style: str = "adjacent"
    tag_key: str = "type"
    content_key: str = "value"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._variants = {}

    @classmethod
    def __from_wire__(cls, data: Any) -> Any:
        if cls.style == "external":
            if isinstance(data, str):
                tag, content = data, None
            else:
                tag = next(iter(data))
                content = data[tag]
        else:
            tag = data[cls.tag_key]
            content = data if cls.style == "internal" else data.get(cls.content_key)

        target = cls._variants.get(tag)
        if target is None:
            raise ValueError(f"Unknown {cls.__name__} variant {tag!r}")

        fields = dataclasses.fields(target)
        if not fields:
            return target()
        if len(fields) == 1 and fields[0].metadata.get("newtype"):
            hints = typing.get_type_hints(target)
            return target(decode(content, hints[fields[0].name]))
        return _decode_dataclass(content, target)


def to_tagged(obj: Any) -> dict:
    """Encode a tagged-union variant instance to its union's wire form."""
    union = getattr(obj, "_union")
    tag = getattr(obj, "_tag")
    fields = dataclasses.fields(obj)

    is_newtype = len(fields) == 1 and fields[0].metadata.get("newtype")
    if is_newtype:
        content: Any = encode(getattr(obj, fields[0].name))
    elif fields:
        # Encode the variant's fields as a map directly; calling encode(obj)
        # here would re-enter __to_wire__ and recurse forever.
        content = {
            f.metadata.get("rename", f.name): encode(getattr(obj, f.name))
            for f in fields
            if not f.metadata.get("skip")
        }
    else:
        content = None

    if union.style == "external":
        return tag if not fields else {tag: content}
    if union.style == "internal":
        out = {union.tag_key: tag}
        if isinstance(content, dict):
            out.update(content)
        return out
    out = {union.tag_key: tag}
    if fields:
        out[union.content_key] = content
    return out
