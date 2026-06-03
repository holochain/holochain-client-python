"""Source-chain ``Record`` types: ``Action`` (and its variants), ``Entry``, and
the wrappers that tie them together.

Zome calls return application data as opaque MessagePack, so the client cannot
type those results automatically. When a zome returns a ``Record`` (or a list of
them), decode it explicitly::

    from holochain_client.types.record import Record, decode_record

    raw = await app.call_zome(cell_id, "my_zome", "get_thing", action_hash)
    record = decode_record(raw)
    record.signed_action.hashed.hash          # ActionHash
    record.action()                            # the Action variant
    record.entry                               # RecordEntry
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..hash import (
    ActionHash,
    AgentPubKey,
    AnyLinkableHash,
    DnaHash,
    EntryHash,
)
from ..serde import TaggedUnion, decode, variant
from .common import Timestamp

# Entry visibility serializes as the bare string "Public" / "Private".
EntryVisibility = str

# A signature is 64 raw bytes; link tags are arbitrary bytes.
Signature = bytes
LinkTag = bytes


def _newtype():
    return field(metadata={"newtype": True})


# --------------------------------------------------------------------------- #
# Entry
# --------------------------------------------------------------------------- #
class MigrationTarget(TaggedUnion):
    style = "external"


@variant(MigrationTarget, "Dna")
@dataclass
class MigrationToDna:
    dna_hash: DnaHash = _newtype()


@variant(MigrationTarget, "Agent")
@dataclass
class MigrationToAgent:
    agent: AgentPubKey = _newtype()


@dataclass
class AppEntryDef:
    entry_index: int
    zome_index: int
    visibility: EntryVisibility


class EntryType(TaggedUnion):
    style = "external"


@variant(EntryType, "AgentPubKey")
@dataclass
class EntryTypeAgentPubKey:
    pass


@variant(EntryType, "App")
@dataclass
class EntryTypeApp:
    app_entry_def: AppEntryDef = _newtype()


@variant(EntryType, "CapClaim")
@dataclass
class EntryTypeCapClaim:
    pass


@variant(EntryType, "CapGrant")
@dataclass
class EntryTypeCapGrant:
    pass


class Entry(TaggedUnion):
    """A source-chain entry. Serialized with ``tag = "entry_type"``."""

    tag_key = "entry_type"
    content_key = "entry"


@variant(Entry, "Agent")
@dataclass
class AgentEntry:
    agent: AgentPubKey = _newtype()


@variant(Entry, "App")
@dataclass
class AppEntry:
    """App entry bytes (MessagePack of the application entry)."""

    bytes: bytes = _newtype()


@variant(Entry, "CapClaim")
@dataclass
class CapClaimEntry:
    value: Any = _newtype()


@variant(Entry, "CapGrant")
@dataclass
class CapGrantEntry:
    value: Any = _newtype()


# --------------------------------------------------------------------------- #
# Action variants (internally tagged: {"type": <variant>, ...fields})
# --------------------------------------------------------------------------- #
class Action(TaggedUnion):
    """A source-chain action."""

    style = "internal"


@variant(Action, "Dna")
@dataclass
class Dna:
    author: AgentPubKey
    timestamp: Timestamp
    hash: DnaHash


@variant(Action, "AgentValidationPkg")
@dataclass
class AgentValidationPkg:
    author: AgentPubKey
    timestamp: Timestamp
    action_seq: int
    prev_action: ActionHash
    membrane_proof: Optional[bytes] = None


@variant(Action, "InitZomesComplete")
@dataclass
class InitZomesComplete:
    author: AgentPubKey
    timestamp: Timestamp
    action_seq: int
    prev_action: ActionHash


@variant(Action, "CreateLink")
@dataclass
class CreateLink:
    author: AgentPubKey
    timestamp: Timestamp
    action_seq: int
    prev_action: ActionHash
    base_address: AnyLinkableHash
    target_address: AnyLinkableHash
    zome_index: int
    link_type: int
    tag: LinkTag
    weight: Any = None


@variant(Action, "DeleteLink")
@dataclass
class DeleteLink:
    author: AgentPubKey
    timestamp: Timestamp
    action_seq: int
    prev_action: ActionHash
    base_address: AnyLinkableHash
    link_add_address: ActionHash


@variant(Action, "CloseChain")
@dataclass
class CloseChain:
    author: AgentPubKey
    timestamp: Timestamp
    action_seq: int
    prev_action: ActionHash
    new_target: Optional[MigrationTarget] = None


@variant(Action, "OpenChain")
@dataclass
class OpenChain:
    author: AgentPubKey
    timestamp: Timestamp
    action_seq: int
    prev_action: ActionHash
    prev_target: MigrationTarget
    close_hash: ActionHash


@variant(Action, "Create")
@dataclass
class Create:
    author: AgentPubKey
    timestamp: Timestamp
    action_seq: int
    prev_action: ActionHash
    entry_type: EntryType
    entry_hash: EntryHash
    weight: Any = None


@variant(Action, "Update")
@dataclass
class Update:
    author: AgentPubKey
    timestamp: Timestamp
    action_seq: int
    prev_action: ActionHash
    original_action_address: ActionHash
    original_entry_address: EntryHash
    entry_type: EntryType
    entry_hash: EntryHash
    weight: Any = None


@variant(Action, "Delete")
@dataclass
class Delete:
    author: AgentPubKey
    timestamp: Timestamp
    action_seq: int
    prev_action: ActionHash
    deletes_address: ActionHash
    deletes_entry_address: EntryHash
    weight: Any = None


# --------------------------------------------------------------------------- #
# Record
# --------------------------------------------------------------------------- #
@dataclass
class ActionHashed:
    """An ``Action`` paired with its ``ActionHash`` (``HoloHashed<Action>``)."""

    content: Action
    hash: ActionHash


@dataclass
class SignedActionHashed:
    hashed: ActionHashed
    signature: Signature


class RecordEntry(TaggedUnion):
    """The entry component of a record: present, hidden, absent, or not stored."""

    style = "external"


@variant(RecordEntry, "Present")
@dataclass
class EntryPresent:
    entry: Entry = _newtype()


@variant(RecordEntry, "Hidden")
@dataclass
class EntryHidden:
    pass


@variant(RecordEntry, "NA")
@dataclass
class EntryNotApplicable:
    pass


@variant(RecordEntry, "NotStored")
@dataclass
class EntryNotStored:
    pass


@dataclass
class Record:
    """A chain record: a signed action and, if applicable, its entry."""

    signed_action: SignedActionHashed
    entry: RecordEntry

    def action(self) -> Any:
        """The decoded ``Action`` variant for this record."""
        return self.signed_action.hashed.content

    def action_hash(self) -> ActionHash:
        return self.signed_action.hashed.hash

    def entry_value(self) -> Optional[Entry]:
        """The ``Entry`` if one is present, else ``None``."""
        if isinstance(self.entry, EntryPresent):
            return self.entry.entry
        return None


def decode_record(data: Any) -> Record:
    """Decode raw MessagePack-decoded data into a :class:`Record`."""
    return decode(data, Record)


def decode_records(data: Any) -> List[Record]:
    """Decode a list of records."""
    return [decode_record(item) for item in data]
