"""Test KNNFewShot compilation with DSPy."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import dspy
from hemdov.domain.dspy_modules.knn_fewshot_learner import KNNFewShotLearner


def test_knn_learner_initialization():
    """Test KNNFewShotLearner can be initialized."""
    learner = KNNFewShotLearner(k=3)
    assert learner.k == 3
    assert learner.trainset is None


def test_knn_learner_compile():
    """Test KNNFewShotLearner compilation with examples."""
    # Create sample trainset
    trainset = [
        dspy.Example(
            original_idea="Create a prompt for code review",
            context="",
            improved_prompt="## Role\nCode Reviewer\n\n## Directive\nReview code for bugs",
            role="Code Reviewer",
            directive="Review code for bugs",
            framework="",
            guardrails="",
        ).with_inputs("original_idea", "context"),
        dspy.Example(
            original_idea="Generate a data analyst prompt",
            context="",
            improved_prompt="## Role\nData Analyst\n\n## Directive\nAnalyze data trends",
            role="Data Analyst",
            directive="Analyze data trends",
            framework="",
            guardrails="",
        ).with_inputs("original_idea", "context"),
    ]

    learner = KNNFewShotLearner(k=1)
    compiled = learner.compile(trainset)

    assert compiled is not None
    assert learner.trainset is not None
    assert len(learner.trainset) == 2
