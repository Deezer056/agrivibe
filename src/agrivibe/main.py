from contextlib import asynccontextmanager

from fastapi import FastAPI

from agrivibe.api import chat, farmer, knowledge, threads
from agrivibe.core.database import open_database
from agrivibe.core.mcp import load_fieldsat
from agrivibe.dependencies import build_chat_service, get_settings
from agrivibe.models.farmer import Farmer
from agrivibe.service.threads import ThreadService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once at startup: load FieldSat's tools and open Postgres. The app refuses to start without either."""
    settings = get_settings()
    fieldsat = await load_fieldsat(settings.fieldsat_url)
    print("FieldSat tools:", ", ".join(tool.name for tool in fieldsat.tools))
    async with open_database(settings.database_url.get_secret_value()) as db:
        print("Postgres: connected; threads and farmer memory persist")
        app.state.thread_service = ThreadService(db.pool, db.checkpointer)
        # The seed: the one farmer this deployment serves (see current_farmer) must exist before they chat.
        await app.state.thread_service.add_farmer(Farmer(id=settings.farmer_id, name=settings.farmer_name))
        app.state.chat_service = build_chat_service(
            settings, fieldsat, db.checkpointer, db.store, app.state.thread_service
        )
        yield


app = FastAPI(
    title="AgriVibe API",
    description="API for the AgriVibe project",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(knowledge.router)
app.include_router(chat.router)
app.include_router(threads.router)
app.include_router(farmer.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
