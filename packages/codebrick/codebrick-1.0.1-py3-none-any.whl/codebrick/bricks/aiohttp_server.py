# coding: utf-8
import os
import aiohttp
from aiohttp import web


async def handle_request(request):
    return web.Response(text="Hello, World!")

async def listfiles(request):
    data = {
        "files": os.listdir('.'),
        "message": "List of files",
        "code": 200,
    }
    return web.json_response(data)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            await ws.send_str(f"Hello, {msg.data}!")
        elif msg.type == aiohttp.WSMsgType.BINARY:
            await ws.send_bytes(msg.data)
        elif msg.type == aiohttp.WSMsgType.CLOSE:
            break
    return ws

app = web.Application()
app.router.add_get('/', handle_request)
app.router.add_get('/files', listfiles)
app.router.add_get('/ws', websocket_handler)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8000)
