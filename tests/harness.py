from os import write
from subprocess import Popen, run, PIPE
import signal

class TestHarness:
    async def __aenter__(self):
        self._sandbox_process = start_holochain()

    async def __aexit__(self, exc_type, exc, tb):
        del exc_type, exc, tb
        self._sandbox_process.send_signal(signal.SIGINT)

def start_holochain() -> Popen:
    ps = run(["hc", "sandbox", "clean"])
    if ps.returncode != 0:
        raise Exception("Failed to clean sandbox")

    ps = run(["hc", "sandbox", "--piped", "create", "--in-process-lair"], text=True, input="passphrase\n")
    if ps.returncode != 0:
        raise Exception("Failed to create sandbox")
    
    ps = Popen(["hc", "sandbox", "--piped", "-f", "8888", "run"], stdin=PIPE, stdout=PIPE, text=True)
    ps.stdin.write("passphrase\n")
    ps.stdin.flush()

    ps.stdout.readline()
    ps.stdout.readline()
    ps.stdout.readline()
    ps.stdout.readline()

    return ps
