import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import scenes, patches, ingest
from app.database import create_tables

app = FastAPI(title="Writers Room X", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(scenes.router, prefix="/api", tags=["scenes"])
app.include_router(patches.router, prefix="/api", tags=["patches"])

# Static files for uploads
os.makedirs("data", exist_ok=True)
os.makedirs("data/manuscript", exist_ok=True)
os.makedirs("data/codex", exist_ok=True)

@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
async def root():
    return {"message": "Writers Room X API", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
