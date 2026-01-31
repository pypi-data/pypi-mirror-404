import json
from contextlib import asynccontextmanager
from typing import Any

import websockets.asyncio.client
from websockets.asyncio.client import ClientConnection


@asynccontextmanager
async def connect(endpoint: str):
    async with websockets.asyncio.client.connect(endpoint) as ws:
        yield Sockem(ws)


class Sockem:
    _conn: ClientConnection

    def __init__(self, conn: ClientConnection) -> None:
        self._conn = conn
        pass

    async def send(self, channel: str, data: Any):
        await self._conn.send(json.dumps({"name": channel, "data": data}))

    async def authenticate(self, code: str):
        await self.send("__sockem:authenticate", code)
        return await self.receive_one()

    async def listen(self, channel: str):
        await self.send("__sockem:listen", channel)
        return await self.receive_one()

    async def receive_one(self) -> dict:
        return json.loads(await self._conn.recv())

    async def receive(self):
        async for msg in self._conn.recv_streaming():
            yield dict(json.loads(msg))
