from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from database import init_db
from rag.vector_store import init_vector_store
from agents.market_agent import start_price_refresh
from routers import auth_router, scan_router, chat_router, market_router, weather_router, community_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🌱 Starting AgriMind AI Backend...")
    init_db()
    init_vector_store()
    start_price_refresh()  # loads live mandi prices in the background
    Path("uploads").mkdir(exist_ok=True)
    print("✅ AgriMind ready!")
    yield
    # Shutdown
    print("👋 AgriMind shutting down")

app = FastAPI(
    title="AgriMind AI API",
    description="Agentic AI backend for smart crop intelligence",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routers
app.include_router(auth_router.router)
app.include_router(scan_router.router)
app.include_router(chat_router.router)
app.include_router(market_router.router)
app.include_router(weather_router.router)
app.include_router(community_router.router)

@app.get("/")
def root():
    return {"status": "AgriMind AI Backend running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}