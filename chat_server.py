"""
Standalone Chat Server - Serves chat.html and proxies requests to the main Kraftd backend
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json

app = FastAPI(title="Kraftd Chat UI")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to chat.html
CHAT_FILE = Path(__file__).parent / "frontend" / "chat.html"
BACKEND_URL = "http://localhost:8000"


@app.get("/")
async def root():
    """Redirect to chat."""
    return {"message": "Chat UI available at /chat"}


@app.get("/chat")
async def get_chat():
    """Serve the chat UI."""
    if not CHAT_FILE.exists():
        raise HTTPException(status_code=404, detail="Chat UI file not found")
    return FileResponse(CHAT_FILE, media_type="text/html")


@app.post("/api/v1/chat")
async def chat(request: dict):
    """Proxy chat requests to the main backend."""
    try:
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # For now, return a demo response
        # In production, this would forward to the main backend
        return {
            "response": f"I received your message: '{message}'. The main Kraftd backend is starting up. Please try again in a moment.",
            "conversation_id": "demo-1"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Kraftd Chat UI Server",
        "chat_ui_available": CHAT_FILE.exists()
    }


if __name__ == "__main__":
    import uvicorn
    print(f"Chat UI file: {CHAT_FILE}")
    print(f"File exists: {CHAT_FILE.exists()}")
    uvicorn.run(app, host="127.0.0.1", port=3000)
