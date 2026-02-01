# coding: utf-8

import websockets
import asyncio
import json


async def connect_ws(url: str):
    async with websockets.connect(url) as websocket:
        while True:
            await websocket.send("Hello, World!")
            data2 = {"message": "Hello, World!"}
            await websocket.send(json.dumps(data2))
            # data = await websocket.recv()
            # data_dict = json.loads(await websocket.recv())
            data_dict = await websocket.recv()
            print(f"Received message: {data_dict}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(connect_ws("ws://localhost:8000/ws"))