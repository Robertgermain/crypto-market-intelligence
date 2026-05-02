from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(title="Crypto Market Intelligence")

# --------------------------------------------------
# Health Check (keep this exactly as you wanted)
# --------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}


# --------------------------------------------------
# API v1 Routes
# --------------------------------------------------
app.include_router(api_router, prefix="/api/v1")