[![Project](https://img.shields.io/badge/Project-Holochain-blue.svg?style=flat-square)](http://holochain.org/)
[![Discord](https://img.shields.io/badge/Discord-DEV.HC-blue.svg?style=flat-square)](https://discord.gg/k55DS5dmPH)
[![License: CAL 1.0](https://img.shields.io/badge/License-CAL%201.0-blue.svg)](https://github.com/holochain/cryptographic-autonomy-license)
[![Twitter Follow](https://img.shields.io/twitter/follow/holochain.svg?style=social&label=Follow)](https://twitter.com/holochain)

# Holochain Client - Python

A Python client for the [Holochain](https://holochain.org/) Conductor API, targeting **Holochain 0.6**.

It speaks the admin and app websocket interfaces directly: msgpack framing, the
`{type, value}` request/response envelope, fully-typed request/response models,
and client-side zome-call signing (msgpack + SHA-512 + ed25519 via PyNaCl — no
native dependency).

> [!NOTE]
> Unstable-feature endpoints (countersigning, DNA migration) are not yet covered.

### Usage

```python
from holochain_client import AdminClient, AppClient, AppBundlePath

admin = await AdminClient.connect("ws://localhost:4444")
app_info = await admin.install_app(
    AppBundlePath(path="my-app.happ"), installed_app_id="my-app"
)
await admin.enable_app("my-app")

cell_id = app_info.cell_info["my-role"][0].cell_id
port = await admin.attach_app_interface(allowed_origins="*")
token = await admin.issue_app_authentication_token("my-app")

app = await AppClient.connect(f"ws://localhost:{port}", token.token)
app.credentials.set(cell_id, await admin.authorize_signing_credentials(cell_id))

result = await app.call_zome(cell_id, "my_zome", "my_fn", {"some": "payload"})
```

### Set up a development environment

The developer environment for this project relies on Holonix, which you can find out more about in the Holochain [getting started guide](https://developer.holochain.org/get-started/). Once you have Nix installed, you can create a new development environment by entering the following command into your shell at the root of this project:

```bash
nix develop
```

Then once the Nix shell has spawned, create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Then install dependencies using Poetry:

```bash
poetry install --no-root
```

Running the tests is a good way to check your development environment!

### Run the tests

The tests rely on a fixture. The fixture is a simple Holochain app that contains a single zome. It must be built before running the tests. You can do this using:

```bash
cd fixture
npm install
npm run build:happ
cd ..
```

If that succeeds then the tests will be able to find the built happ and you can move on to running the tests.

You can run all the tests using:

```bash
poetry run pytest
```

To select a single test suite, pass the path to `pytest`. For example:

```bash
poetry run pytest tests/app/test_zome_call.py
```

To run a single test, pass the path to the test suite and then use the `-k` flag. For example:

```bash
poetry run pytest tests/app/test_zome_call.py -k test_echo
```

The integration tests boot a real conductor with `hc sandbox`. To run them
against an already-running conductor instead, set `HC_ADMIN_PORT` to its admin
port. The unit tests (`tests/test_serde.py`, `tests/test_signing.py`) need no
conductor.

> [!TIP]
> By default `pytest` captures output. Use the `-s` flag in combination with `RUST_LOG=info` to debug tests against Holochain.

### Keep the code tidy

Linting and formatting are done by one tool, [Ruff](https://docs.astral.sh/ruff/). Run the linter using:

```bash
poetry run ruff check
```

If you want it to automatically fix the problems it finds, then use:

```bash
poetry run ruff check --fix
```

Run the formatter using:

```bash
poetry run ruff format
```
