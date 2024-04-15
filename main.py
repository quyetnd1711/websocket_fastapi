import uvicorn
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dataclasses import dataclass
from typing import Dict
import uuid
import json
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

templates = Jinja2Templates(directory="templates")


@dataclass
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        id_web = str(uuid.uuid4())
        self.active_connections[id_web] = websocket

        await self.send_message(websocket, json.dumps({"isMe": True, "data": "Welcome to the chat room", "username": "You"}))

    async def send_message(self, ws: WebSocket, message: str):
        await ws.send_text(message)

    def find_connection_id(self, websocket: WebSocket):
        websocket_list = list(self.active_connections.values())
        id_list = list(self.active_connections.keys())

        pos = websocket_list.index(websocket)
        return id_list[pos]

    async def broadcast(self, webSocket: WebSocket, data: str):
        decoded_data = json.loads(data)

        for connection in self.active_connections.values():
            is_me = False
            if connection == webSocket:
                is_me = True

            await connection.send_text(
                json.dumps({"isMe": is_me, "data": decoded_data['message'], "username": decoded_data['username']}))

    def disconnect(self, websocket: WebSocket):
        id_web = self.find_connection_id(websocket)
        del self.active_connections[id_web]
        return id_web


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
connection_manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
def get_room(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/message")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the connection from the client.
    await connection_manager.connect(websocket)
    try:
        while True:
            # Receives message from the client
            data = await websocket.receive_text()
            await connection_manager.broadcast(websocket, data)
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
        return RedirectResponse("/")


@app.get("/join", response_class=HTMLResponse)
def get_room(request: Request):
    return templates.TemplateResponse("room.html", {"request": request})