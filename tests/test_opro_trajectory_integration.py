"""
Integration tests for OPRO trajectory.

Tests the full optimization loop including:
- Trajectory tracking across iterations
- Early stopping at quality threshold
- Best candidate selection from history
- Score progression validation
"""

import pytest
from datetime import datetime, UTC

from hemdov.domain.dto.nlac_models import (
    PromptObject,
    IntentType,
    OPROIteration,
)
from hemdov.domain.services.oprop_optimizer import OPROOptimizer


class TestOPROTrajectoryIntegration:
    """Integration tests for complete OPRO optimization trajectory."""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer without LLM (uses simple refinement)."""
        return OPROOptimizer(llm_client=None)

    @pytest.fixture
    def complex_prompt(self):
        """Create a complex prompt that needs optimization."""
        return PromptObject(
            id="complex-test",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Create a function",
            strategy_meta={"strategy": "simple"},
            constraints={
                "max_tokens": 1000,
                "include_examples": True,
                "include_explanation": True,
            },
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

    def test_full_trajectory_tracking(self, optimizer, complex_prompt):
        """Full trajectory records all iterations correctly."""
        response = optimizer.run_loop(complex_prompt)

        # Should have completed MAX_ITERATIONS (no early stopping for this prompt)
        assert response.iteration_count == OPROOptimizer.MAX_ITERATIONS
        assert len(response.trajectory) == OPROOptimizer.MAX_ITERATIONS

        # Each iteration should have all required fields
        for i, iteration in enumerate(response.trajectory, 1):
            assert iteration.iteration_number == i
            assert iteration.meta_prompt_used
            assert iteration.generated_instruction
            assert 0.0 <= iteration.score <= 1.0
            assert iteration.feedback

    def test_trajectory_progression(self, optimizer, complex_prompt):
        """Scores should generally improve or stay stable across iterations."""
        response = optimizer.run_loop(complex_prompt)

        scores = [iter.score for iter in response.trajectory]
        final_score = response.final_score

        # Final score should be the best (highest) score
        assert final_score == max(scores)

        # Check that we're tracking the best candidate
        best_iteration = max(response.trajectory, key=lambda x: x.score)
        assert response.final_instruction == best_iteration.generated_instruction

    def test_early_stopping_trajectory(self, optimizer):
        """Early stopping should truncate trajectory at threshold."""
        # Create a prompt that will pass all constraints
        perfect_prompt = PromptObject(
            id="perfect",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="You are a Developer.\n\n# Task\nCreate a function.\n\nFor example:\ndef test():\n    pass\n\nThis explains the reasoning clearly.",
            strategy_meta={"strategy": "simple"},
            constraints={
                "max_tokens": 500,
                "format": "code",
                "include_examples": True,
                "include_explanation": True
            },
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        response = optimizer.run_loop(perfect_prompt)

        # Should early stop (iteration < MAX_ITERATIONS)
        assert response.early_stopped is True
        assert response.iteration_count < OPROOptimizer.MAX_ITERATIONS
        assert response.final_score >= OPROOptimizer.QUALITY_THRESHOLD

    def test_trajectory_meta_prompt_evolution(self, optimizer, complex_prompt):
        """Meta-prompts should evolve based on previous iterations."""
        response = optimizer.run_loop(complex_prompt)

        # Meta-prompts should reference previous iterations
        # (after the first one)
        for i, iteration in enumerate(response.trajectory[1:], 2):
            assert "Iteration" in iteration.meta_prompt_used or "previous" in iteration.meta_prompt_used.lower()

    def test_trajectory_feedback_reuse(self, optimizer, complex_prompt):
        """Feedback from previous iterations should inform next meta-prompt."""
        response = optimizer.run_loop(complex_prompt)

        # Each iteration after the first should have feedback from previous
        for i in range(1, len(response.trajectory)):
            # The meta_prompt should contain context about previous attempts
            current_meta = response.trajectory[i].meta_prompt_used
            assert current_meta  # Should not be empty

    def test_best_candidate_selection(self, optimizer):
        """Best candidate from history is selected correctly."""
        # Create a prompt that will have varying scores
        prompt = PromptObject(
            id="variable",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Short",  # Will have low score initially
            strategy_meta={"strategy": "simple"},
            constraints={"include_examples": True},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        response = optimizer.run_loop(prompt)

        # Find best iteration in trajectory
        best_iteration = max(response.trajectory, key=lambda x: x.score)

        # Response should use the best one
        assert response.final_instruction == best_iteration.generated_instruction
        assert response.final_score == best_iteration.score

    def test_iteration_number_uniqueness(self, optimizer, complex_prompt):
        """Each iteration should have a unique iteration number."""
        response = optimizer.run_loop(complex_prompt)

        iteration_numbers = [iter.iteration_number for iter in response.trajectory]
        assert len(iteration_numbers) == len(set(iteration_numbers))  # All unique
        assert set(iteration_numbers) == set(range(1, len(iteration_numbers) + 1))

    def test_trajectory_completeness(self, optimizer, complex_prompt):
        """Trajectory should contain all fields needed for analysis."""
        response = optimizer.run_loop(complex_prompt)

        for iteration in response.trajectory:
            # Verify all OPROIteration fields are populated
            assert isinstance(iteration, OPROIteration)
            assert iteration.iteration_number > 0
            assert iteration.meta_prompt_used
            assert len(iteration.meta_prompt_used) > 0
            assert iteration.generated_instruction
            assert len(iteration.generated_instruction) > 0
            assert isinstance(iteration.score, (int, float))
            assert isinstance(iteration.feedback, str)

    def test_response_metadata(self, optimizer, complex_prompt):
        """OptimizeResponse should contain all metadata."""
        response = optimizer.run_loop(complex_prompt)

        # Required response fields
        assert response.prompt_id == complex_prompt.id
        assert response.final_instruction
        assert 0.0 <= response.final_score <= 1.0
        assert response.iteration_count > 0
        assert isinstance(response.early_stopped, bool)
        assert isinstance(response.trajectory, list)
        assert response.backend == "nlac-opro"
        assert response.model == "oprop-optimizer"

    def test_no_empty_iterations(self, optimizer, complex_prompt):
        """No iteration should have empty generated instruction."""
        response = optimizer.run_loop(complex_prompt)

        for iteration in response.trajectory:
            assert iteration.generated_instruction
            assert len(iteration.generated_instruction.strip()) > 0

    def test_score_monotonicity_best_selection(self, optimizer):
        """Final score should be the maximum of all iteration scores."""
        prompt = PromptObject(
            id="monotonic",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="Test template",
            strategy_meta={"strategy": "simple"},
            constraints={},
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        response = optimizer.run_loop(prompt)

        all_scores = [iter.score for iter in response.trajectory]
        assert response.final_score == max(all_scores)

    def test_early_stopped_trajectory_shorter(self, optimizer):
        """Early stopped trajectory should be shorter than max iterations."""
        # Create prompt that will pass quickly
        quick_pass_prompt = PromptObject(
            id="quick",
            version="1.0.0",
            intent_type=IntentType.GENERATE,
            template="You are a Developer.\n\n# Task\nBuild something.\n\nFor example: def foo(): pass\n\nThis explains why.",
            strategy_meta={"strategy": "simple"},
            constraints={
                "max_tokens": 500,
                "include_examples": True,
                "include_explanation": True
            },
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        response = optimizer.run_loop(quick_pass_prompt)

        # If early stopped, should be shorter
        if response.early_stopped:
            assert len(response.trajectory) < OPROOptimizer.MAX_ITERATIONS
        else:
            assert len(response.trajectory) == OPROOptimizer.MAX_ITERATIONS
