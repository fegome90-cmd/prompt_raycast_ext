"""
FastAPI endpoint for Prompt Improver.

Exposes the DSPy PromptImprover module via REST API.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import dspy

from eval.src.dspy_prompt_improver import PromptImprover
from hemdov.infrastructure.config import Settings

router = APIRouter(prefix="/api/v1", tags=["prompts"])


class ImprovePromptRequest(BaseModel):
    idea: str
    context: str = ""


class ImprovePromptResponse(BaseModel):
    improved_prompt: str
    role: str
    directive: str
    framework: str
    guardrails: list[str]
    reasoning: str | None = None
    confidence: float | None = None


# Initialize module (lazy loading)
_prompt_improver: PromptImprover | None = None


def get_prompt_improver(settings: Settings) -> PromptImprover:
    """Get or initialize PromptImprover module."""
    global _prompt_improver

    if _prompt_improver is None:
        # Initialize module
        improver = PromptImprover()

        # Load compiled version if available
        if settings.DSPY_COMPILED_PATH:
            improver.load(settings.DSPY_COMPILED_PATH)
        else:
            # Use uncompiled version
            pass

        _prompt_improver = improver

    return _prompt_improver


@router.post("/improve-prompt", response_model=ImprovePromptResponse)
async def improve_prompt(request: ImprovePromptRequest):
    """
    Improve a raw idea into a high-quality structured prompt.

    POST /api/v1/improve-prompt
    {
        "idea": "Design ADR process",
        "context": "Software architecture team"
    }

    Response:
    {
        "improved_prompt": "**[ROLE & PERSONA]**\\nYou are...",
        "role": "World-Class Software Architect...",
        "directive": "To design and detail...",
        "framework": "chain-of-thought",
        "guardrails": ["Avoid jargon", "Prioritize pragmatism", ...],
        "reasoning": "Selected role for expertise...",
        "confidence": 0.87
    }
    """
    # Validate input
    if not request.idea or len(request.idea.strip()) < 5:
        raise HTTPException(
            status_code=400, detail="Idea must be at least 5 characters"
        )

    # Get module
    from hemdov.interfaces import container

    settings = container.get(Settings)
    improver = get_prompt_improver(settings)

    # Improve prompt
    try:
        result = improver(original_idea=request.idea, context=request.context)

        return ImprovePromptResponse(
            improved_prompt=result.improved_prompt,
            role=result.role,
            directive=result.directive,
            framework=result.framework,
            guardrails=result.guardrails.split("\n")
            if isinstance(result.guardrails, str)
            else result.guardrails,
            reasoning=getattr(result, "reasoning", None),
            confidence=getattr(result, "confidence", None),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Prompt improvement failed: {str(e)}"
        )
