# coding: utf-8
"""
基于 aiohttp 的 WebSocket 客户端，可与 aiohttp_server 的 /ws 端点配合使用。
"""

import aiohttp
import asyncio
import json


async def connect_ws(url: str, ping_interval: float = 20.0, ping_timeout: float = 20.0):
    """
    连接 WebSocket 并维持收发循环。

    Args:
        url: WebSocket 地址，如 ws://localhost:8000/ws
        ping_interval: 心跳间隔（秒）
        ping_timeout: 心跳超时（秒）
    """
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(
            url,
            heartbeat=ping_interval,
            receive_timeout=ping_timeout,
        ) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print(f"Received text: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    print(f"Received binary: {len(msg.data)} bytes")
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    print("Connection closed")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"Connection error: {ws.exception()}")
                    break


async def connect_ws_send_recv(
    url: str,
    send_interval: float = 1.0,
    message: str = "Hello, World!",
):
    """
    连接 WebSocket，按间隔发送消息并打印收到的消息（与 ws_client 行为类似）。

    Args:
        url: WebSocket 地址
        send_interval: 发送间隔（秒）
        message: 要发送的文本消息
    """
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            while True:
                # 发送文本
                await ws.send_str(message)
                # 发送 JSON
                await ws.send_str(json.dumps({"message": message}))

                # 接收（带超时，避免一直阻塞）
                try:
                    msg = await asyncio.wait_for(ws.receive(), timeout=send_interval + 5)
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        print(f"Received: {msg.data}")
                    elif msg.type == aiohttp.WSMsgType.BINARY:
                        print(f"Received binary: {len(msg.data)} bytes")
                    elif msg.type == aiohttp.WSMsgType.CLOSE:
                        print("Connection closed by server")
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"Error: {ws.exception()}")
                        break
                except asyncio.TimeoutError:
                    pass

                await asyncio.sleep(send_interval)


if __name__ == "__main__":
    # 与 codebrick/bricks/aiohttp_server.py 的 /ws 端点配合
    asyncio.run(connect_ws_send_recv("ws://localhost:8000/ws"))
