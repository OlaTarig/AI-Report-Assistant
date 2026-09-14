from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, conversations, files, messages, reports
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="AI Report Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/api/health")
async def health():
    return {"status": "ok"}
