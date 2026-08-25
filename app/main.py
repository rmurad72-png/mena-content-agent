from fastapi import FastAPI

app = FastAPI(
    title="MENA Content Agent",
    version="0.1.0"
)


@app.get("/")
async def root():
    return {
        "name": "MENA Content Agent",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": "production"
    }
