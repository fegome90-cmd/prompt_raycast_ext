"""Tests for ExampleValidator."""

from scripts.synthetic_examples.validator import TASK_TYPES, ExampleValidator


def test_validate_example_missing_question():
    """Should reject example without question field"""
    validator = ExampleValidator()

    example = {
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": 0.9,
            "source_component_id": "test.md",
            "variation": "base",
        }
    }

    result = validator.validate_single_example(example)

    assert result["is_valid"] is False
    assert any(e["field"] == "question" for e in result["errors"])


def test_validator_rejects_invalid_examples():
    """Should reject low-quality examples"""
    validator = ExampleValidator()

    invalid_examples = [
        {
            "question": "Hi",  # Too short (< 50)
            "metadata": {
                "task_type": "role_definition",
                "domain": "aiml",
                "confidence": 0.9,
                "source_component_id": "test.md",
                "variation": "base",
            },
        },
        {
            "question": "x" * 5001,  # Too long (> 5000)
            "metadata": {
                "task_type": "role_definition",
                "domain": "aiml",
                "confidence": 0.9,
                "source_component_id": "test.md",
                "variation": "base",
            },
        },
        {
            "question": "You are an assistant. Using Chain-of-Thought, answer: What is AI?",
            "metadata": {
                "task_type": "framework_application",
                "domain": "aiml",
                "confidence": 0.9,
                "source_component_id": "test.md",
                "variation": "base",
            },
        },
    ]

    for example in invalid_examples:
        result = validator.validate_single_example(example)
        assert result["is_valid"] is False


def test_validator_accepts_valid_example():
    """Should accept valid high-quality example"""
    validator = ExampleValidator()

    example = {
        "question": "You are an expert AI researcher. Explain machine learning concepts with clear examples. Provide detailed explanations with step-by-step reasoning. Avoid technical jargon where possible.",
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": 0.9,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    result = validator.validate_single_example(example)

    assert result["is_valid"] is True
    assert result["score"] > 0.5
    assert len(result["errors"]) == 0


def test_validator_checks_question_length_range():
    """Should validate question length is within bounds"""
    validator = ExampleValidator()

    example_just_above_min = {
        "question": "You are an expert in the field of artificial intelligence.",
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": 0.9,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    example_just_below_max = {
        "question": "x" * 5000,  # Exactly MAX_QUESTION_LENGTH
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": 0.9,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    result1 = validator.validate_single_example(example_just_above_min)
    result2 = validator.validate_single_example(example_just_below_max)

    # First example should be valid (good content, within bounds)
    assert result1["is_valid"] is True
    # Second example should be invalid due to low quality (repetitive)
    assert result2["is_valid"] is False


def test_validator_detects_empty_fields():
    """Should detect empty role or directive fields"""
    validator = ExampleValidator()

    example = {
        "question": " . ",
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": 0.9,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    result = validator.validate_single_example(example)

    assert result["is_valid"] is False
    assert any("empty" in e["message"].lower() for e in result["errors"])


def test_validator_detects_framework_mentions():
    """Should reject examples mentioning specific frameworks"""
    validator = ExampleValidator()

    example_with_chain_of_thought = {
        "question": "You are an expert. Using Chain-of-Thought, answer the question.",
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": 0.9,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    example_with_tree_of_thoughts = {
        "question": "Apply Tree-of-Thoughts to solve this problem.",
        "metadata": {
            "task_type": "framework_application",
            "domain": "aiml",
            "confidence": 0.9,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    result1 = validator.validate_single_example(example_with_chain_of_thought)
    result2 = validator.validate_single_example(example_with_tree_of_thoughts)

    assert result1["is_valid"] is False
    assert result2["is_valid"] is False


def test_validator_calculates_quality_score():
    """Should calculate quality score between 0.0 and 1.0"""
    validator = ExampleValidator()

    high_quality = {
        "question": "You are a senior software engineer with expertise in distributed systems. Explain microservices architecture with practical examples. Include constraints about scalability and provide clear action verbs for implementation.",
        "metadata": {
            "task_type": "role_definition",
            "domain": "softdev",
            "confidence": 0.95,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    result = validator.validate_single_example(high_quality)

    assert 0.0 <= result["score"] <= 1.0
    assert result["score"] > 0.7


def test_validator_batch_validation():
    """Should validate batch of examples with min quality score threshold"""
    validator = ExampleValidator()

    examples = [
        {
            "question": "x" * 60,  # Valid but low quality
            "metadata": {
                "task_type": "role_definition",
                "domain": "aiml",
                "confidence": 0.9,
                "source_component_id": "test.md",
                "variation": "base",
            },
        },
        {
            "question": "You are an expert researcher. Provide detailed analysis with examples and specific constraints for implementation.",
            "metadata": {
                "task_type": "role_definition",
                "domain": "aiml",
                "confidence": 0.9,
                "source_component_id": "test.md",
                "variation": "base",
            },
        },
    ]

    valid_examples, stats = validator.validate_batch(examples, min_quality_score=0.5)

    assert len(valid_examples) == 1
    assert stats["total"] == 2
    assert stats["valid"] == 1
    assert stats["invalid"] == 1


def test_validator_detects_special_characters():
    """Should detect excessive special characters"""
    validator = ExampleValidator()

    example = {
        "question": "You are an expert. @#$%^&*()_+=-[]{}|;':\",./<>?~`",
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": 0.9,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    result = validator.validate_single_example(example)

    assert result["is_valid"] is False
    assert any("special" in e["message"].lower() for e in result["errors"])


def test_validator_detects_unbalanced_parentheses():
    """Should detect unbalanced parentheses"""
    validator = ExampleValidator()

    example = {
        "question": "You are an expert (with deep knowledge. Explain the concept.",
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": 0.9,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    result = validator.validate_single_example(example)

    assert result["is_valid"] is False
    assert any("parentheses" in e["message"].lower() for e in result["errors"])


def test_validator_detects_repetition():
    """Should detect repetitive content"""
    validator = ExampleValidator()

    example = {
        "question": "You are an expert. You are an expert. You are an expert. You are an expert.",
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": 0.9,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    result = validator.validate_single_example(example)

    assert result["is_valid"] is False
    assert any("repetition" in e["message"].lower() for e in result["errors"])


def test_validator_detects_missing_metadata():
    """Should reject examples with missing metadata"""
    validator = ExampleValidator()

    example = {
        "question": "You are an expert in AI.",
    }

    result = validator.validate_single_example(example)

    assert result["is_valid"] is False
    assert any("metadata" in e["field"].lower() for e in result["errors"])


def test_validator_detects_invalid_task_type():
    """Should reject examples with invalid task_type"""
    validator = ExampleValidator()

    example = {
        "question": "You are an expert in AI.",
        "metadata": {
            "task_type": "invalid_type",
            "domain": "aiml",
            "confidence": 0.9,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    result = validator.validate_single_example(example)

    assert result["is_valid"] is False
    assert any("task_type" in e["message"].lower() for e in result["errors"])


def test_validator_detects_invalid_confidence():
    """Should reject examples with invalid confidence values"""
    validator = ExampleValidator()

    example_too_low = {
        "question": "You are an expert in AI.",
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": -0.1,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    example_too_high = {
        "question": "You are an expert in AI.",
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": 1.1,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    result1 = validator.validate_single_example(example_too_low)
    result2 = validator.validate_single_example(example_too_high)

    assert result1["is_valid"] is False
    assert result2["is_valid"] is False
    assert any("confidence" in e["message"].lower() for e in result1["errors"])
    assert any("confidence" in e["message"].lower() for e in result2["errors"])


def test_validator_returns_warnings():
    """Should return warnings for non-critical issues"""
    validator = ExampleValidator()

    example = {
        "question": "You are an expert. This is acceptable but minimal.",
        "metadata": {
            "task_type": "role_definition",
            "domain": "aiml",
            "confidence": 0.6,
            "source_component_id": "test.md",
            "variation": "base",
        },
    }

    result = validator.validate_single_example(example)

    assert "warnings" in result
    assert isinstance(result["warnings"], list)


def test_task_types_constant():
    """TASK_TYPES should contain all required task types"""
    required_types = [
        "role_definition",
        "directive_task",
        "framework_application",
        "guardrail_extraction",
        "combined_task",
    ]

    for task_type in required_types:
        assert task_type in TASK_TYPES


def test_validator_initialization():
    """Should initialize with default quality thresholds"""
    validator = ExampleValidator()

    assert validator.MIN_QUESTION_LENGTH == 50
    assert validator.MAX_QUESTION_LENGTH == 5000
    assert validator.MIN_GUARDRAILS == 1
    assert validator.MAX_GUARDRAILS == 10
