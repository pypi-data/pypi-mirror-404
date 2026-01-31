from fastapi import FastAPI

app = FastAPI(title="${project_name}")

@app.get("/health")
async def health():
    return {"status": "ok"}