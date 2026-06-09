# main.py — The entry point for the FastAPI application
# 
# When you run "uvicorn main:app", Python:
# 1. Imports this file
# 2. Finds the "app" variable
# 3. Starts the web server

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, chat
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create the FastAPI application
app = FastAPI(
    title="Dive in PDF API",
    description="Upload PDFs and chat with them using AI",
    version="1.0.0"
)

# ─── CORS SETUP ───
# CORS = Cross-Origin Resource Sharing
# Without this, your browser would BLOCK the React app from calling this API
# (because React runs on localhost:5173 and API runs on localhost:8000)
#
# In development, we allow all origins.
# In production, you should set this to your actual frontend URL.

allowed_origins = [
    "http://localhost:5173",          # Local React dev server (Vite)
    "http://localhost:3000",          # Alternative React port
    os.getenv("FRONTEND_URL", ""),    # Production frontend URL from env
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o for o in allowed_origins if o
    ],  # Filter out empty strings
    allow_credentials=True,
    allow_methods=["*"],      # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],      # Allow all headers
)

# ─── REGISTER ROUTES ───
# These connect URL paths to your router files
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


# ─── HEALTH CHECK ───
@app.get("/")
async def root():
    """Basic health check endpoint."""
    """Visit http://localhost:8000/ to verify the server is running."""
    return {
        "status": "running",
        "message": "PDF Chat API is running! Visit /docs for the API."
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}