"""
Main FastAPI application for DSPy Prompt Improver backend.

This server exposes the PromptImprover module via REST API for integration
with the Raycast TypeScript frontend.
"""

import logging
import os
from contextlib import asynccontextmanager
from enum import Enum

import dspy
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.rate_limiter import limiter

from api.exception_utils import create_exception_handlers
from api.metrics_api import router as metrics_router
from api.middleware import RequestIDMiddleware
from api.prompt_history_api import router as history_router
from api.prompt_improver_api import router as prompt_improver_router
from hemdov.infrastructure.adapters.litellm_dspy_adapter_prompt import (
    create_anthropic_adapter,
    create_deepseek_adapter,
    create_gemini_adapter,
    create_ollama_adapter,
    create_openai_adapter,
)
from hemdov.infrastructure.config import settings
from hemdov.infrastructure.persistence.metrics_repository import SQLiteMetricsRepository
from hemdov.interfaces import container

# Global LM instance for DSPy
lm = None

# Temperature defaults per provider (for consistency)
DEFAULT_TEMPERATURE = {
    "ollama": 0.1,    # Local models need some variability
    "gemini": 0.0,    # Gemini is deterministic at 0.0
    "deepseek": 0.0,  # CRITICAL: 0.0 for maximum consistency
    "openai": 0.0,    # OpenAI is deterministic at 0.0
    "anthropic": 0.0, # Anthropic is deterministic at 0.0
}

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - initialize DSPy LM."""
    global lm

    # Initialize DSPy with appropriate LM
    provider = settings.LLM_PROVIDER.lower()
    temp = DEFAULT_TEMPERATURE.get(provider, 0.0)

    if provider == "ollama":
        lm = create_ollama_adapter(
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL,
            temperature=temp,  # Uses 0.1 from DEFAULT_TEMPERATURE
        )
    elif provider == "gemini":
        lm = create_gemini_adapter(
            model=settings.LLM_MODEL,
            api_key=settings.GEMINI_API_KEY or settings.LLM_API_KEY,
            temperature=temp,  # Uses 0.0 from DEFAULT_TEMPERATURE
        )
    elif provider == "deepseek":
        lm = create_deepseek_adapter(
            model=settings.LLM_MODEL,
            api_key=settings.DEEPSEEK_API_KEY or settings.LLM_API_KEY,
            temperature=temp,  # Uses 0.0 from DEFAULT_TEMPERATURE
        )
    elif provider == "openai":
        lm = create_openai_adapter(
            model=settings.LLM_MODEL,
            api_key=settings.OPENAI_API_KEY or settings.LLM_API_KEY,
            temperature=temp,  # Uses 0.0 from DEFAULT_TEMPERATURE
        )
    elif provider == "anthropic":
        lm = create_anthropic_adapter(
            model=settings.LLM_MODEL,
            api_key=(
                settings.ANTHROPIC_API_KEY
                or settings.HEMDOV_ANTHROPIC_API_KEY
                or settings.LLM_API_KEY
            ),
            base_url=settings.LLM_BASE_URL,
            temperature=temp,  # Uses 0.0 from DEFAULT_TEMPERATURE
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    # Configure DSPy
    dspy.settings.configure(lm=lm)

    # Register metrics repository for metrics endpoints
    try:
        metrics_db_path = "data/metrics.db"  # Separate from prompt_history.db
        metrics_repo = SQLiteMetricsRepository(metrics_db_path)
        await metrics_repo.initialize()  # Must call async initialize before use
        container.register(SQLiteMetricsRepository, metrics_repo)
        logger.info("SQLiteMetricsRepository registered in container")
    except (ConnectionError, OSError, RuntimeError) as e:
        logger.warning(f"Failed to initialize metrics repository: {type(e).__name__}: {e}")

    logger.info(f"DSPy configured with {settings.LLM_PROVIDER}/{settings.LLM_MODEL}")

    yield

    logger.info("Shutting down DSPy backend...")
    await container.shutdown()


# Create FastAPI app
app = FastAPI(
    title="DSPy Prompt Improver API",
    description="Backend service for improving raw ideas into structured SOTA prompts using DSPy",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda req, exc: HTTPException(
    status_code=429, detail="Rate limit exceeded. Please try again later."
))
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
cors_origins = (
    ["*"]
    if settings.CORS_ORIGINS == "*"
    else [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware for tracing
app.add_middleware(RequestIDMiddleware)


class CSPMiddleware(BaseHTTPMiddleware):
    """Add Content-Security-Policy headers for static files."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com;"
            )
        return response


app.add_middleware(CSPMiddleware)

# Include routers
app.include_router(prompt_improver_router)
app.include_router(metrics_router)
app.include_router(history_router)

# Mount static files for prompt viewer UI (with existence check)
static_dir = "static"
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning(f"Static directory '{static_dir}' not found, viewer will be unavailable")

# Register global exception handlers
exception_handlers = create_exception_handlers()
for exc_type, handler in exception_handlers.items():
    app.add_exception_handler(exc_type, handler)


# Health check endpoint
class HealthState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@app.get("/health")
async def health_check(
    simulate: HealthState = Query(
        default=HealthState.HEALTHY,
        description="Simulate health state for testing"
    )
):
    """
    Health check endpoint with state simulation for testing.

    Security note: In production, consider rate limiting this endpoint
    to prevent DoS attacks. Use nginx rate limiting or similar.
    """
    # Block simulation in production environment
    if simulate != HealthState.HEALTHY and os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(
            status_code=403,
            detail="Simulation not allowed in production environment"
        )

    if simulate == HealthState.UNAVAILABLE:
        raise HTTPException(status_code=503, detail="Service unavailable (simulated)")

    if simulate == HealthState.DEGRADED:
        return {
            "status": "degraded",
            "provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL,
            "dspy_configured": lm is not None,
            "degradation_flags": {"knn_disabled": True}
        }

    return {
        "status": "healthy",
        "provider": settings.LLM_PROVIDER,
        "model": settings.LLM_MODEL,
        "dspy_configured": lm is not None,
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "DSPy Prompt Improver API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "improve_prompt": "/api/v1/improve-prompt",
            "evaluate_quality": "/api/v1/evaluate-quality",
            "history": "/api/v1/history/",
            "history_search": "/api/v1/history/search",
            "history_stats": "/api/v1/history/stats",
            "viewer": "/static/viewer.html",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn

    # Validate configuration on startup (fail fast)
    if not (1024 <= settings.API_PORT <= 65535):
        raise ValueError(f"Invalid API_PORT: {settings.API_PORT}. Must be between 1024-65535.")

    # Validate API key for cloud providers
    if settings.LLM_PROVIDER.lower() == "deepseek":
        if not settings.DEEPSEEK_API_KEY:
            raise ValueError(
                "DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek. "
                "Get your API key from https://platform.deepseek.com/"
            )
        if not settings.DEEPSEEK_API_KEY.startswith("sk-"):
            raise ValueError(
                "Invalid DEEPSEEK_API_KEY format. "
                "Expected 'sk-...' prefix."
            )
        # Log key configured for verification (no key data exposed)
        logger.info("DeepSeek API key configured: true")

    elif settings.LLM_PROVIDER.lower() == "gemini":
        if not settings.GEMINI_API_KEY and not settings.LLM_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is required when LLM_PROVIDER=gemini"
            )

    elif settings.LLM_PROVIDER.lower() == "openai":
        if not settings.OPENAI_API_KEY and not settings.LLM_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai"
            )

    elif settings.LLM_PROVIDER.lower() == "anthropic":
        if (
            not settings.ANTHROPIC_API_KEY
            and not settings.HEMDOV_ANTHROPIC_API_KEY
            and not settings.LLM_API_KEY
        ):
            raise ValueError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
            )

    logger.info("Starting DSPy Prompt Improver API...")
    logger.info("✓ Configuration loaded from .env")
    logger.info(f"✓ API_PORT: {settings.API_PORT} (validated)")
    logger.info(f"Server: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"LLM: {settings.LLM_PROVIDER}/{settings.LLM_MODEL}")
    if settings.LLM_PROVIDER.lower() in ["deepseek", "gemini", "openai", "anthropic"]:
        logger.info("✓ Cloud provider configured - API validation passed")

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
