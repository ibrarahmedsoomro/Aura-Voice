import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router

app = FastAPI(
    title="Aura Voice (VOXAGENT) API",
    description="Autonomous AI Voice Agent Architecture",
    version="1.0.0"
)

# CORS configuration for Frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix="/api")

# Mount exports directory for direct file serving
base_dir = os.path.dirname(os.path.abspath(__file__))
exports_dir = os.path.join(base_dir, "exports")
os.makedirs(exports_dir, exist_ok=True)
app.mount("/exports", StaticFiles(directory=exports_dir), name="exports")

@app.get("/")
def health_check():
    return {
        "status": "online",
        "agent": "Aura Voice (VOXAGENT)",
        "capabilities": [
            "Autonomous QC",
            "Surgical Chunk Repair",
            "Voice Consistency Lock",
            "Multi-lingual (En, Ur, Hi, Roman Urdu)",
            "Word/Sentence Timelines (SRT/VTT/JSON)"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
