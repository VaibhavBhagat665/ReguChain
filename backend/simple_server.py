"""
Simple test server to verify FastAPI is working
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="ReguChain Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "ReguChain backend is running!"}

@app.get("/api/test")
def test_endpoint():
    return {
        "status": "ok",
        "message": "Test endpoint working",
        "apis": {
            "groq": "configured",
            "newsapi": "configured",
            "pathway": "configured"
        }
    }

if __name__ == "__main__":
    print("Starting simple test server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
