[![Project](https://img.shields.io/badge/Project-Holochain-blue.svg?style=flat-square)](http://holochain.org/)
[![Discord](https://img.shields.io/badge/Discord-DEV.HC-blue.svg?style=flat-square)](https://discord.gg/k55DS5dmPH)
[![License: CAL 1.0](https://img.shields.io/badge/License-CAL%201.0-blue.svg)](https://github.com/holochain/cryptographic-autonomy-license)
[![Twitter Follow](https://img.shields.io/twitter/follow/holochain.svg?style=social&label=Follow)](https://twitter.com/holochain)

# Holochain Client - Python

> [!WARNING]
> :radioactive: This package is under development, it is not a complete Holochain client and is not fully tested! :radioactive:

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
poetry run tests/api/app/client_test.py
```

To run a single test, pass the path to the test suite and the use the `-k` flag. For example:

```bash
poetry run pytest tests/api/app/client_test.py -k test_call_zome
```

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
