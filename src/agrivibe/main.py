from fastapi import FastAPI

app = FastAPI(
    title="AgriVibe API",
    description="API for the AgriVibe project",
    version="0.1.0",
   
)

@app.get("/health", tags=["system"])
def health () -> dict[str, str]:
    return {"status": "ok"}
    