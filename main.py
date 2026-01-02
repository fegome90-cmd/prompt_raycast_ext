"""
Main FastAPI application for DSPy Prompt Improver backend.

This server exposes the PromptImprover module via REST API for integration
with the Raycast TypeScript frontend.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from hemdov.infrastructure.config import settings
from hemdov.interfaces import container
from hemdov.infrastructure.adapters.litellm_dspy_adapter_prompt import (
    create_ollama_adapter,
    create_gemini_adapter,
    create_deepseek_adapter,
    create_openai_adapter,
)
from api.prompt_improver_api import router as prompt_improver_router
import dspy

# Global LM instance for DSPy
lm = None

# Temperature defaults per provider (for consistency)
DEFAULT_TEMPERATURE = {
    "ollama": 0.1,    # Local models need some variability
    "gemini": 0.0,    # Gemini is deterministic at 0.0
    "deepseek": 0.0,  # CRITICAL: 0.0 for maximum consistency
    "openai": 0.0,    # OpenAI is deterministic at 0.0
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
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    # Configure DSPy
    dspy.settings.configure(lm=lm)

    logger.info(f"DSPy configured with {settings.LLM_PROVIDER}/{settings.LLM_MODEL}")

    yield

    logger.info("Shutting down DSPy backend...")


# Create FastAPI app
app = FastAPI(
    title="DSPy Prompt Improver API",
    description="Backend service for improving raw ideas into structured SOTA prompts using DSPy",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prompt_improver_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
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
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn

    # Validate configuration on startup (fail fast)
    if not (1024 <= settings.API_PORT <= 65535):
        raise ValueError(f"Invalid API_PORT: {settings.API_PORT}. Must be between 1024-65535.")

    logger.info("Starting DSPy Prompt Improver API...")
    logger.info(f"✓ Configuration loaded from .env")
    logger.info(f"✓ API_PORT: {settings.API_PORT} (validated)")
    logger.info(f"Server: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"LLM: {settings.LLM_PROVIDER}/{settings.LLM_MODEL}")

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
