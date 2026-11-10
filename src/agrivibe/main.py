from contextlib import asynccontextmanager

from fastapi import FastAPI

from agrivibe.api import ask, chat, knowledge
from agrivibe.core.database import open_memory
from agrivibe.core.mcp import load_fieldsat
from agrivibe.dependencies import build_chat_service, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once at startup: load FieldSat's tools and open Postgres. The app refuses to start without either."""
    settings = get_settings()
    fieldsat = await load_fieldsat(settings.fieldsat_url)
    print("FieldSat tools:", ", ".join(tool.name for tool in fieldsat.tools))
    async with open_memory(settings.database_url.get_secret_value()) as (checkpointer, store):
        print("Postgres: connected; threads and farmer memory persist")
        app.state.chat_service = build_chat_service(settings, fieldsat, checkpointer, store)
        yield

app = FastAPI(
    title="AgriVibe API",
    description="API for the AgriVibe project",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(knowledge.router)
app.include_router(ask.router)
app.include_router(chat.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
