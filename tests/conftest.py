import pytest_asyncio

from tests.harness import Harness


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def harness():
    async with Harness() as h:
        yield h
