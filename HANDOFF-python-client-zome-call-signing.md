# Handoff: Zome-call signing for a Holochain Python client

**Audience:** an agent building/maintaining the downstream Python client library for Holochain.
**Date:** 2026-06-03. **Holochain target at time of writing:** 0.6.1.

## TL;DR

Do **not** depend on a native serialization crate (the `holochain-serialization-python`
pyo3 binding — now **archived**). The JS client (`@holochain/client`) dropped its
equivalent (`holochain-serialization-js`) and now signs zome calls with plain
**msgpack + sha512 + ed25519**, entirely in-language. A Python client should do the
same with `msgpack` + `hashlib.sha512` + `PyNaCl`. No Rust, no `maturin`, no
per-platform wheels, no chasing Holochain crate versions.

## Why the native serialization lib is obsolete

Old model (pre-0.4-ish): the client sent **structured** zome-call params; the
conductor re-serialized them with its canonical Rust serializer and hashed the
result. Client and conductor therefore had to serialize **byte-identically**, which
is why a Rust binding existed — to reuse the exact `holochain_serialized_bytes`
encoder. (`holochain-serialization-python::get_data_to_sign` reflects this: it
returns only the 32-/now-64-byte **hash**, not the bytes.)

Current model: the client serializes the params itself, signs the hash of *those*
bytes, and transmits **both the bytes and the signature** as `CallZomeRequestSigned
{ bytes, signature }`. The conductor verifies by hashing the **received bytes** — it
does **not** re-serialize. Consequence: the client's serialization no longer has to
match any canonical Rust impl. Any msgpack encoding the conductor can deserialize
into `ZomeCallParams` works, in any field order. That removed the entire reason for
the serialization library.

## Reference implementation (TypeScript, authoritative)

Repo `holochain/holochain-client-js`, branch `main`:

- `src/api/app/websocket.ts:652` — `signZomeCall(request)`. The core:
  ```ts
  const zome_call_params = {
    cap_secret, cell_id, zome_name, fn_name, provenance,
    payload: encode(request.payload),   // payload is itself msgpack-encoded first
    nonce: await randomNonce(),
    expires_at: getNonceExpiration(),
  };
  const bytes     = encode(zome_call_params);     // @msgpack/msgpack
  const bytesHash = new Uint8Array(sha512.array(bytes));   // js-sha512
  const signature = sodium.crypto_sign(bytesHash, keyPair.privateKey)
                          .subarray(0, sodium.crypto_sign_BYTES); // detached, 64 bytes
  return { bytes, signature };          // CallZomeRequestSigned
  ```
- `src/api/zome-call-signing.ts` — signing keypair, nonce, cap-secret, credential store.
- `src/api/admin/websocket.ts:324` — `grantSigningKey` / `authorizeSigningCredentials`.
- `src/utils/hash-parts.ts` — HoloHash byte layout & type prefixes.

Relevant runtime deps in the JS client `package.json` (no serialization lib):
`@msgpack/msgpack`, `js-sha512`, `@bitgo/blake2b`, `libsodium-wrappers`,
`js-base64`, `lodash-es`.

## The signing algorithm, precisely

1. **Signing keypair is ephemeral**, not the agent's real key. Generate an ed25519
   keypair; authorize it on the conductor via the admin API (below). Store
   `{ capSecret, keyPair, signingKey }` per `cellId`.
2. **`signingKey` (= `provenance`)** is a 39-byte AgentPubKey holohash:
   `[132, 32, 36]` (Agent prefix) + 32-byte ed25519 public key + 4-byte DHT location.
   The JS client fakes the location as the last 4 bytes of a supplied agent key, else
   `[0,0,0,0]`. Hash layout (from `hash-parts.ts`): 3-byte type prefix + 32-byte core
   + 4-byte location = 39 bytes. Agent prefix `[132,32,36]`, Dna `[132,45,36]`, etc.
3. **`payload` is double-encoded**: msgpack-encode the call payload first, then it
   becomes a `bytes` field inside the params map that is msgpack-encoded again.
4. **`expires_at`** = `(now_ms + 5*60*1000) * 1000` → microseconds since epoch (i64).
5. **`nonce`** = 32 random bytes. **`cap_secret`** = 64 bytes (or `None`/absent if the
   grant is unrestricted).
6. **`cell_id`** is a 2-element array `[dna_hash(39B), agent_pubkey(39B)]`.
7. Serialize the params map with msgpack, `sha512` the bytes, ed25519-sign the **hash**
   (detached 64-byte signature), send `{ bytes, signature }`.

## Python implementation guidance

```python
import time, secrets, hashlib, msgpack
from nacl.signing import SigningKey          # PyNaCl; wraps libsodium ed25519

def now_micros_plus_5min() -> int:
    return (int(time.time() * 1000) + 5 * 60 * 1000) * 1000

def sign_zome_call(*, cell_id, zome_name, fn_name, payload,
                   provenance, cap_secret, signing_key: SigningKey):
    params = {
        "cap_secret": cap_secret,                       # bytes(64) or None
        "cell_id": [cell_id[0], cell_id[1]],            # [dna_hash, agent_pubkey], 39B each
        "zome_name": zome_name,                         # str
        "fn_name": fn_name,                             # str
        "provenance": provenance,                       # 39-byte signing AgentPubKey
        "payload": msgpack.packb(payload, use_bin_type=True),
        "nonce": secrets.token_bytes(32),
        "expires_at": now_micros_plus_5min(),
    }
    data = msgpack.packb(params, use_bin_type=True)
    bytes_hash = hashlib.sha512(data).digest()
    signature = signing_key.sign(bytes_hash).signature  # 64-byte detached ed25519 sig
    return {"bytes": data, "signature": signature}      # CallZomeRequestSigned
```

### Correctness pitfalls (will silently produce a rejected signature)

- **`use_bin_type=True` is mandatory.** Byte fields (hashes, nonce, cap_secret,
  pre-encoded payload) must serialize as msgpack `bin`, not `str`. Equivalent to JS
  encoding `Uint8Array`.
- **Pass `bytes`, not `list[int]`,** for all byte fields so msgpack picks `bin`.
- **Field order doesn't matter for correctness** (conductor hashes received bytes),
  but you MUST hash exactly the bytes you transmit. Don't re-encode between hashing
  and sending.
- **ed25519 key material:** libsodium `crypto_sign` secret keys are 64 bytes
  (seed+pubkey); PyNaCl `SigningKey` takes a 32-byte seed. Use one consistently and
  make sure the public key embedded in `provenance` matches the private key you sign
  with. Prefer `nacl.bindings.crypto_sign_*` if you need byte-exact libsodium parity.
- Sign the **sha512 hash**, not the raw bytes.

### Capability authorization (required before any signed call works)

Mirror `AdminWebsocket.authorizeSigningCredentials` / `grantSigningKey`
(`src/api/admin/websocket.ts:324`):

1. Generate ephemeral signing keypair → derive 39-byte `signingKey`.
2. `randomCapSecret()` = 64 random bytes.
3. Admin call `grant_zome_call_capability` with:
   ```
   cap_grant: {
     tag: "zome-call-signing-key",
     functions: { type: "all" }  // or { type: "listed", value: [[zome, fn], ...] }
     access: { type: "assigned", value: { secret: capSecret, assignees: [signingKey] } }
   }
   ```
4. Store `{ capSecret, keyPair, signingKey }` keyed by `cellId`; reuse for signing.

## Suggested Python deps

`msgpack` (the `msgpack` PyPI package), `PyNaCl` (ed25519 / libsodium). `hashlib`
covers sha512 from stdlib. msgpack/admin transport is WebSocket — pick an async ws
client (e.g. `websockets`). No native build toolchain required.

## Open items to verify against a live 0.6.1 conductor

- Exact admin `grant_zome_call_capability` request shape on the **Python** transport
  (field names are snake_case on the wire; cross-check the conductor API for 0.6.1).
- Whether `cap_secret` should be **absent** vs explicit `None` for unrestricted
  grants — match what the conductor's serde expects (`Option<CapSecret>`).
- Confirm `CallZomeRequestSigned` is the accepted request variant name in 0.6.1.
- App-authentication token flow (`issue_app_authentication_token`) precedes app-ws
  calls in the JS client — replicate it.

## Don't

- Don't revive the pyo3 `holochain-serialization-python` crate. It's archived, it ties
  you to specific Holochain crate versions (painful: every Holochain bump is a port —
  e.g. 0.2→0.6 renamed `ZomeCallUnsigned`→`ZomeCallParams`, `data_to_sign()`→
  `serialize_and_hash()`, changed the hash from blake2b/32B to sha512/64B), and it
  only returns the hash anyway — which is the wrong shape for the send-the-bytes
  protocol.
