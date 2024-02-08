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

TODO: How to verify your development environment?
