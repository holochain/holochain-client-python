from subprocess import Popen, run, PIPE
import signal
import re
import json
from typing import Tuple
from holochain_client.api.admin.client import AdminClient
from pathlib import Path
from os import path

class TestHarness:
    admin_client: AdminClient
    fixture_path: str

    async def __aenter__(self):
        (self._sandbox_process, admin_port) = _start_holochain()
        self.admin_client = await AdminClient.create(f"ws://localhost:{admin_port}")

        fixture_path = (Path(__file__).parent / "../fixture/workdir/fixture.happ").resolve()
        if not path.exists(fixture_path):
            raise Exception("Fixture does not exist, please build it before running this test")
        self.fixture_path = str(fixture_path)

        return self

    async def __aexit__(self, exc_type, exc, tb):
        del exc_type, exc, tb
        await self.admin_client.close()
        self._sandbox_process.send_signal(signal.SIGINT)


def _start_holochain() -> Tuple[Popen, int]:
    ps = run(["hc", "sandbox", "clean"])
    if ps.returncode != 0:
        raise Exception("Failed to clean sandbox")

    ps = run(
        ["hc", "sandbox", "--piped", "create", "--in-process-lair"],
        text=True,
        input="passphrase\n",
    )
    if ps.returncode != 0:
        raise Exception("Failed to create sandbox")

    ps = Popen(["hc", "sandbox", "--piped", "run"], stdin=PIPE, stdout=PIPE, text=True)
    ps.stdin.write("passphrase\n")
    ps.stdin.flush()

    # TODO if the sandbox fails to start or print the expected magic line, this loop won't exit
    admin_port = 0
    while True:
        line = ps.stdout.readline()
        match = re.search(r"#!0 (.*)", line)
        if match:
            info = json.loads(match.group(1))
            admin_port = info["admin_port"]
            break

    return (ps, admin_port)
