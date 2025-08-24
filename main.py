from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException,Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import random


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# In-memory user store: name → user_id
users = {}
# Active WebSocket connections: websocket → user_id
connected_users = {}

# Generate user ID based on name
def generate_user_id(name: str):
    return f"{name}_{random.randint(100, 999)}"

# Request model for signup/login
class User(BaseModel):
    name: str

@app.post("/signup")
def signup(user: User):
    if user.name in users:
        raise HTTPException(status_code=400, detail="User already exists")
    user_id = generate_user_id(user.name)
    users[user.name] = user_id
    return {"user_id": user_id}

@app.post("/login")
def login(user: User):
    if user.name not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": users[user.name]}



@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connected_users[websocket] = user_id

    await broadcast(f"{user_id} has joined the chat.")

    try:
        while True:
            data = await websocket.receive_text()
            #await websocket.send_text(f"You wrote: {data}")
            await broadcast(f"{user_id}: {data}")
    except WebSocketDisconnect:
        del connected_users[websocket]
        await broadcast(f"{user_id} has left the chat.")

async def broadcast(message: str):
    for connection in connected_users:
        await connection.send_text(message)