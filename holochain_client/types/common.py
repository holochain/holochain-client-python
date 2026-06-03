"""Common scalar type aliases shared across the conductor API.

These mirror the Rust newtypes/aliases. They are documentation-only aliases:
the wire representation is the underlying primitive.
"""

from __future__ import annotations

# String identifiers.
ZomeName = str
FunctionName = str
RoleName = str
InstalledAppId = str
NetworkSeed = str

# Microseconds since the Unix epoch (Holochain ``Timestamp``).
Timestamp = int

# Raw byte secrets / tokens.
CapSecret = bytes  # 64 bytes
Nonce = bytes  # 32 bytes
AppAuthenticationToken = bytes
