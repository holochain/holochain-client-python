from typing import Optional
import asyncio
import websockets

class AdminClient:
    @classmethod
    async def create(cls, url: str, defaultTimeout: Optional[int] = None):
        self = cls()
        self.client = await websockets.connect(url)
        self.defaultTimeout = defaultTimeout
        return self

    async def close(self):
        await self.client.close()
