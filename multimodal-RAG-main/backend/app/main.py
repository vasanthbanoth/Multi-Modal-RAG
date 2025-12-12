import time
import logging
from fastapi import FastAPI, Request
from backend.app.api.v1 import endpoints
from backend.app.api.v1 import auth

# Import service instances to ensure they are initialized on startup
from backend.app.services.embedding import embedding_service
from backend.app.services.vector_db import vector_db_service
from backend.app.services.storage_service import storage_service
from backend.app.services.llm_gen import generative_service
from backend.app.services.parser import document_service

# Reference the instances so static analysis doesn't flag them as unused
_services = (embedding_service, vector_db_service, storage_service, generative_service, document_service)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the main FastAPI app instance.
app = FastAPI(
    title="Multi-RAG API",
    description="A multi-modal RAG API using FastAPI, Pinecone, and Google Gemini.",
    version="1.0.0"
)

# Add middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Example middleware to add a custom X-Process-Time header
    to all API responses.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.on_event("startup")
async def startup_event():
    """
    Application startup event. This is where you can initialize resources.
    """
    logger.info("--- Application Startup ---")
    # By importing the service instances, we ensure they are initialized.
    logger.info("Services are being initialized...")

# --- Mount API Routers ---
# This includes all the core application routes (query, embeddings, etc.)
# from the 'endpoints.py' module under the /api/v1 prefix.
app.include_router(endpoints.router, prefix="/api/v1", tags=["Core API"])
# This includes all the authentication-related routes (login, get user, etc.)
# from the 'auth.py' module under the /api/v1/auth prefix.
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])