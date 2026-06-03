# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Rewritten as a canonical client for **Holochain 0.6**. The conductor wire
  protocol is implemented directly: msgpack framing, the `{type, value}`
  envelope, and fully-typed admin/app request and response models.
- Zome-call signing is now done in-language with `msgpack` + `hashlib.sha512` +
  `PyNaCl`, dropping the archived native `holochain-serialization` dependency.
- Response deserialization into typed models (HoloHashes, `CellId`, `AppInfo`,
  `CellInfo`, capability grants, …) via a type-driven serde layer.
- Async-only API surface (`AdminClient`, `AppClient`).
- Test fixture upgraded to Holochain 0.6 (hdk 0.6 / hdi 0.7, current DNA/app
  manifest format).
- Tooling moved to Python 3.10+ and the modern Holonix flake.
