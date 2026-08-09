from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import documents, chat, auth
from app.services.vector_store import init_vector_collection

# ==========================================
# 1. FastAPI Application Lifecycle Setup
# ==========================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-Grade Multi-Tenant Agentic RAG Cloud Gateway",
    version="1.0.0"
)

# ==========================================
# 2. CORS Firewall Exception Configuration
# ==========================================
# Allows our Next.js dashboard to communicate with this backend securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, swap with your exact Vercel frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 3. Database Lifecycle Boot Hook
# ==========================================
@app.on_event("startup")
async def on_startup():
    """
    Executes the moment the web server launches. 
    Verifies and provisions cloud vector assets instantly.
    """
    print("🛸 App booting up... Verifying cloud infrastructure state.")
    init_vector_collection(collection_name="contextiq_knowledge")

# ==========================================
# 4. Route Blueprint Assembly Mounts
# ==========================================
app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")

@app.get("/", tags=["Health Check"])
async def root_health_check():
    """
    Basic service endpoint confirming system availability.
    """
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "engine": "LangGraph Agentic Loop Active"
    }