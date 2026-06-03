"""Test harness that boots a real Holochain conductor sandbox.

Requires the ``hc`` and ``holochain`` binaries on ``PATH`` (provided by Holonix
in CI). The fixture hApp must be built first (``cd fixture && npm run
build:happ``).
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from holochain_client.admin import AdminClient
from holochain_client.app import AppClient
from holochain_client.types.cell import CellId, ProvisionedCell

FIXTURE_HAPP = (Path(__file__).parent / "../fixture/workdir/fixture.happ").resolve()
PASSPHRASE = "test-phrase\n"


class Harness:
    """A running conductor with the fixture app installed and connected."""

    admin: AdminClient
    app: AppClient
    cell_id: CellId
    installed_app_id: str

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None

    async def __aenter__(self) -> "Harness":
        if not FIXTURE_HAPP.exists():
            raise RuntimeError(
                f"fixture hApp not found at {FIXTURE_HAPP}; build it with "
                "`cd fixture && npm run build:happ`"
            )
        # ``HC_ADMIN_PORT`` lets the suite run against an already-running
        # conductor instead of spawning one (useful where spawning is awkward).
        existing_port = os.environ.get("HC_ADMIN_PORT")
        if existing_port:
            admin_port = int(existing_port)
        else:
            self._process, admin_port = _start_conductor()

        self.admin = await AdminClient.connect(f"ws://localhost:{admin_port}")
        self.installed_app_id = "fixture"
        try:
            await self.admin.uninstall_app(self.installed_app_id, force=True)
        except Exception:
            pass
        app_info = await self.admin.install_app(
            _bundle_source(),
            installed_app_id=self.installed_app_id,
        )
        await self.admin.enable_app(self.installed_app_id)

        provisioned = app_info.cell_info["fixture"][0]
        assert isinstance(provisioned, ProvisionedCell)
        self.cell_id = provisioned.cell_id

        app_port = await self.admin.attach_app_interface(allowed_origins="*")
        token = await self.admin.issue_app_authentication_token(self.installed_app_id)
        self.app = await AppClient.connect(f"ws://localhost:{app_port}", token.token)

        credentials = await self.admin.authorize_signing_credentials(self.cell_id)
        self.app.credentials.set(self.cell_id, credentials)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            await self.app.close()
            await self.admin.close()
        finally:
            if self._process is not None:
                self._process.send_signal(signal.SIGINT)
                try:
                    self._process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    self._process.kill()


def _bundle_source():
    from holochain_client.admin.types import AppBundleBytes

    return AppBundleBytes(bundle=FIXTURE_HAPP.read_bytes())


def _start_conductor() -> Tuple[subprocess.Popen, int]:
    subprocess.run(["hc", "sandbox", "clean"], check=False)
    created = subprocess.run(
        ["hc", "sandbox", "--piped", "create", "--in-process-lair"],
        input=PASSPHRASE,
        text=True,
    )
    if created.returncode != 0:
        raise RuntimeError("failed to create sandbox")

    process = subprocess.Popen(
        ["hc", "sandbox", "--piped", "run"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert process.stdin is not None and process.stdout is not None
    process.stdin.write(PASSPHRASE)
    process.stdin.flush()

    while True:
        line = process.stdout.readline()
        if line == "":
            raise RuntimeError("conductor exited before reporting its admin port")
        match = re.search(r"#!0 (.*)", line)
        if match:
            return process, json.loads(match.group(1))["admin_port"]
