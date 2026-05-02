from fastapi import FastAPI

from app.api.v1.router import api_router
from app.api.v1 import decisions

app = FastAPI(title="Crypto Market Intelligence",)

# --------------------------------------------------
# Health Check (keep this exactly as you wanted)
# --------------------------------------------------
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


# --------------------------------------------------
# API v1 Routes
# --------------------------------------------------
app.include_router(api_router, prefix="/api/v1")
app.include_router(decisions.router)