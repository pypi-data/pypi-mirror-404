import uvicorn
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
from fastapi import WebSocket

app = FastAPI(docs_url="/docs", redoc_url="/redoc")
app.openapi_version = "3.0.2"

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}


@app.get("/")
def read_root(q: str = Query(default="fastapi")):
    return {"message": q}


@app.get("/metrics")
async def get_metrics():
    return {"metrics": "metrics"}

# ws连接示例：按消息类型处理（与 aiohttp 一致：TEXT / BINARY / CLOSE）
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if "text" in message:
                text = message["text"]
                print(f"Received text: {text}")
                await websocket.send_text(f"Message received: {text}")
            elif "bytes" in message:
                binary = message["bytes"]
                print(f"Received binary: {len(binary)} bytes")
                await websocket.send_bytes(binary)
    except Exception as e:
        print(f"WebSocket error: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
