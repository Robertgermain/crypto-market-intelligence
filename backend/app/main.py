from fastapi import FastAPI

app = FastAPI(title="Crypto Market Intelligence")

@app.get("/health")
def health_check():
    return {"status": "ok"}