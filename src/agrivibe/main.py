from fastapi import FastAPI
from agrivibe.api import ask
from agrivibe.api import knowledge

app = FastAPI(
    title="AgriVibe API",
    description="API for the AgriVibe project",
    version="0.1.0",

)

app.include_router(knowledge.router)
app.include_router(ask.router)

@app.get("/health", tags=["system"])
def health () -> dict[str, str]:
    return {"status": "ok"}
    