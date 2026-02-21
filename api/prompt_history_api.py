"""Prompt History API - Read-only endpoints for prompt viewer."""

import asyncio

from fastapi import APIRouter, Query, Request

from api.rate_limiter import limiter
from hemdov.domain.entities.prompt_history import PromptHistory
from hemdov.domain.repositories.prompt_repository import PromptRepository
from hemdov.infrastructure.config import Settings
from hemdov.infrastructure.persistence.sqlite_prompt_repository import SQLitePromptRepository
from hemdov.interfaces import container

router = APIRouter(prefix="/api/v1/history", tags=["history"])

# Module-level lock for thread-safe repository initialization
_repo_lock = asyncio.Lock()


async def _get_repo() -> PromptRepository:
    """Get or create repository from DI container."""
    # Fast path: already registered
    try:
        return container.get(PromptRepository)
    except ValueError:
        pass  # Not registered yet, need to create

    # Slow path: create with lock to prevent race condition
    async with _repo_lock:
        # Double-check after acquiring lock (another coroutine may have created it)
        try:
            return container.get(PromptRepository)
        except ValueError:
            # Not registered yet - create and register
            settings = container.get(Settings)
            repo = SQLitePromptRepository(settings)
            container.register(PromptRepository, repo)

            # Register cleanup hook
            async def cleanup() -> None:
                await repo.close()

            container.add_cleanup_hook(cleanup)
            return repo


def _to_dict(prompt: PromptHistory) -> dict:
    """Convert PromptHistory entity to JSON-serializable dict."""
    return {
        "original_idea": prompt.original_idea,
        "context": prompt.context,
        "improved_prompt": prompt.improved_prompt,
        "role": prompt.role,
        "directive": prompt.directive,
        "framework": prompt.framework,
        "guardrails": prompt.guardrails,
        "reasoning": prompt.reasoning,
        "confidence": prompt.confidence,
        "backend": prompt.backend,
        "model": prompt.model,
        "provider": prompt.provider,
        "latency_ms": prompt.latency_ms,
        "created_at": prompt.created_at,
    }


@router.get("/")
@limiter.limit("60/minute")
async def list_prompts(
    request: Request,  # Required for rate limiting
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    provider: str | None = None,
    backend: str | None = None,
) -> dict:
    """List recent prompts with optional filters."""
    repo = await _get_repo()
    prompts = await repo.find_recent(
        limit=limit,
        offset=offset,
        provider=provider,
        backend=backend,
    )
    return {
        "prompts": [_to_dict(p) for p in prompts],
        "count": len(prompts),
        "limit": limit,
        "offset": offset,
    }


@router.get("/search")
@limiter.limit("60/minute")
async def search_prompts(
    request: Request,  # Required for rate limiting
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict:
    """Search prompts by text content."""
    repo = await _get_repo()
    prompts = await repo.search(query=q, limit=limit)
    return {
        "prompts": [_to_dict(p) for p in prompts],
        "count": len(prompts),
        "query": q,
    }


@router.get("/stats")
@limiter.limit("60/minute")
async def get_stats(request: Request) -> dict:  # request required for rate limiting
    """Get usage statistics."""
    repo = await _get_repo()
    return await repo.get_statistics()
