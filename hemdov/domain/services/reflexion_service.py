"""
ReflexionService - Iterative refinement for DEBUG scenario.

Implements Reflexion loop (MultiAIGCD Scenario II):
  Generate → Execute → If fails, inject error → Retry

Converges in 1-2 iterations vs 3 for OPRO (-33% latency).
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Callable

logger = logging.getLogger(__name__)


@dataclass
class ReflexionResult:
    """Result of Reflexion refinement loop."""
    code: str
    iteration_count: int
    success: bool
    error_history: list[str] = field(default_factory=list)
    final_error: Optional[str] = None


class ReflexionService:
    """
    Reflexion-based iterative refinement service.

    Used for DEBUG scenario (MultiAIGCD Scenario II) where we have:
    - The bug (observable behavior)
    - The error (stack trace, exception)

    Reflexion is faster than OPRO for debugging:
    - OPRO: 3 iterations (meta-prompt evolution)
    - Reflexion: 1-2 iterations (error feedback)

    Reference: https://arxiv.org/abs/2303.11366
    """

    def __init__(self, llm_client=None, executor: Optional[Callable] = None):
        """
        Initialize ReflexionService.

        Args:
            llm_client: LLM client for code generation
            executor: Optional execution function (for validation)
                     If None, skips execution and assumes success
        """
        self.llm_client = llm_client
        self.executor = executor

    def refine(
        self,
        prompt: str,
        error_type: str,
        error_message: str = None,
        max_iterations: int = 2,
        initial_context: str = None
    ) -> ReflexionResult:
        """
        Run Reflexion loop to fix/debug code.

        Args:
            prompt: Original debugging prompt
            error_type: Type of error (e.g., "ZeroDivisionError")
            error_message: Optional error details
            max_iterations: Max refinement iterations (default: 2)
            initial_context: Optional code context

        Returns:
            ReflexionResult with final code and iteration history
        """
        error_history = []
        current_prompt = self._build_initial_prompt(
            prompt,
            error_type,
            error_message,
            initial_context
        )

        for iteration in range(1, max_iterations + 1):
            logger.info(f"Reflexion iteration {iteration}/{max_iterations}")

            # Generate code
            try:
                if self.llm_client:
                    code = self.llm_client.generate(current_prompt)
                else:
                    # Fallback for testing
                    code = f"# Generated code for iteration {iteration}"
            except Exception as e:
                # LLM generation failed - abort with error
                logger.exception(
                    f"LLM generation failed at iteration {iteration}/{max_iterations}. "
                    f"Error: {type(e).__name__}"
                )
                return ReflexionResult(
                    code="",
                    iteration_count=iteration,
                    success=False,
                    error_history=error_history + [str(e)],
                    final_error=f"LLM generation failed: {e}"
                )

            # Try to execute if executor provided
            if self.executor:
                try:
                    result = self.executor(code)
                    # Success!
                    logger.info(f"Reflexion converged in {iteration} iterations")
                    return ReflexionResult(
                        code=code,
                        iteration_count=iteration,
                        success=True,
                        error_history=error_history
                    )
                except Exception as e:
                    # Execution failed - add error to context
                    error_msg = str(e)
                    error_history.append(error_msg)
                    logger.exception(
                        f"Executor failed at iteration {iteration}/{max_iterations}. "
                        f"Error: {type(e).__name__}"
                    )

                    # Build prompt with error feedback for next iteration
                    if iteration < max_iterations:
                        current_prompt = self._build_feedback_prompt(
                            current_prompt,
                            code,
                            error_msg
                        )
            else:
                # No executor - assume success after first iteration
                logger.info(f"Reflexion generated code (no execution validation)")
                return ReflexionResult(
                    code=code,
                    iteration_count=iteration,
                    success=True,
                    error_history=error_history
                )

        # Max iterations reached
        logger.warning(f"Reflexion did not converge after {max_iterations} iterations")
        return ReflexionResult(
            code=code,  # Return last generated code
            iteration_count=max_iterations,
            success=False,
            error_history=error_history,
            final_error=error_history[-1] if error_history else None
        )

    def _build_initial_prompt(
        self,
        prompt: str,
        error_type: str,
        error_message: str = None,
        context: str = None
    ) -> str:
        """Build initial debugging prompt."""
        parts = [
            "# Role",
            "You are an expert debugger specializing in Python error diagnosis.",
            "",
            "# Task",
            f"Debug and fix this {error_type}:",
            "",
            prompt,
        ]

        if error_message:
            parts.extend([
                "",
                "# Error Details",
                error_message,
            ])

        if context:
            parts.extend([
                "",
                "# Code Context",
                "```",
                context,
                "```",
            ])

        parts.extend([
            "",
            "# Instructions",
            "1. Identify the root cause",
            "2. Provide a corrected version of the code",
            "3. Include comments explaining the fix",
        ])

        return "\n".join(parts)

    def _build_feedback_prompt(
        self,
        previous_prompt: str,
        previous_code: str,
        error_message: str
    ) -> str:
        """Build prompt with error feedback for next iteration."""
        return f"""{previous_prompt}

# Previous Attempt
```python
{previous_code}
```

# Error
The previous attempt failed with:
{error_message}

# Instructions
Please fix the error above. Address the specific error message provided.
"""
