from fastapi import FastAPI
from routers import auth, rooms, settings
from websocket import handler as websocket

app = FastAPI()
app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(settings.router)
app.include_router(websocket.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
