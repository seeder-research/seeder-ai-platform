from fastapi import FastAPI
import app.models  # noqa: F401 — registers every table with Base.metadata before any request is handled
from app.api import auth, admin, connectors, chats, models, ws

app = FastAPI(title="AI Platform Backend")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(connectors.router)
app.include_router(chats.router)
app.include_router(models.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
