from contextlib import asynccontextmanager

from fastapi import FastAPI

from agrivibe.api import ask, knowledge
from agrivibe.core.mcp import load_fieldsat
from agrivibe.dependencies import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once at startup: connect to FieldSat and load its tools. The app refuses to start without it."""
    fieldsat = await load_fieldsat(get_settings().fieldsat_url)
    print("FieldSat tools:", ", ".join(tool.name for tool in fieldsat.tools))
    yield


app = FastAPI(
    title="AgriVibe API",
    description="API for the AgriVibe project",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(knowledge.router)
app.include_router(ask.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
