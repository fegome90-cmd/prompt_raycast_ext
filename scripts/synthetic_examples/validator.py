"""Quality validation for synthetic examples."""

import re

TASK_TYPES = [
    "role_definition",
    "directive_task",
    "framework_application",
    "guardrail_extraction",
    "combined_task",
]


FRAMEWORKS = [
    "Chain-of-Thought",
    "Tree-of-Thoughts",
]


class ExampleValidator:
    """Validates quality of synthetic prompt examples."""

    MIN_QUESTION_LENGTH = 50
    MAX_QUESTION_LENGTH = 5000
    MIN_GUARDRAILS = 1
    MAX_GUARDRAILS = 10

    def __init__(self):
        """Initialize validator with default thresholds."""
        pass

    def validate_single_example(self, example: dict) -> dict:
        """Validate a single example.

        Args:
            example: Dictionary with 'question' and 'metadata' fields

        Returns:
            Dict with 'is_valid', 'score', 'errors', 'warnings'
        """
        errors = []
        warnings = []

        # Check required fields
        if "question" not in example:
            errors.append(
                {
                    "field": "question",
                    "message": "Missing 'question' field",
                    "severity": "error",
                }
            )

        if "metadata" not in example:
            errors.append(
                {
                    "field": "metadata",
                    "message": "Missing 'metadata' field",
                    "severity": "error",
                }
            )
        else:
            # Validate metadata
            metadata_errors = self._validate_metadata(example["metadata"])
            errors.extend(metadata_errors)

        # Validate question if present
        if "question" in example:
            question = example["question"]

            # Check length
            if len(question) < self.MIN_QUESTION_LENGTH:
                errors.append(
                    {
                        "field": "question",
                        "message": f"Question too short ({len(question)} < {self.MIN_QUESTION_LENGTH})",
                        "severity": "error",
                    }
                )

            if len(question) > self.MAX_QUESTION_LENGTH:
                errors.append(
                    {
                        "field": "question",
                        "message": f"Question too long ({len(question)} > {self.MAX_QUESTION_LENGTH})",
                        "severity": "error",
                    }
                )

            # Pattern checks
            pattern_errors = self._check_patterns(question)
            errors.extend(pattern_errors)

        # Calculate quality score
        score = self._calculate_quality_score(example, errors, warnings)

        is_valid = len(errors) == 0 and score > 0.5

        return {
            "is_valid": is_valid,
            "score": score,
            "errors": errors,
            "warnings": warnings,
        }

    def validate_batch(
        self, examples: list[dict], min_quality_score: float = 0.5
    ) -> tuple[list[dict], dict]:
        """Validate a batch of examples.

        Args:
            examples: List of example dictionaries
            min_quality_score: Minimum quality score threshold

        Returns:
            Tuple of (valid_examples, statistics_dict)
        """
        valid_examples = []
        total = len(examples)
        valid = 0
        invalid = 0
        scores = []

        for example in examples:
            result = self.validate_single_example(example)

            if result["is_valid"] and result["score"] >= min_quality_score:
                valid_examples.append(example)
                valid += 1
            else:
                invalid += 1

            scores.append(result["score"])

        stats = {
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "avg_score": sum(scores) / len(scores) if scores else 0.0,
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
        }

        return valid_examples, stats

    def _validate_metadata(self, metadata: dict) -> list[dict]:
        """Validate metadata fields.

        Args:
            metadata: Metadata dictionary

        Returns:
            List of error dictionaries
        """
        errors = []

        required_fields = [
            "task_type",
            "domain",
            "confidence",
            "source_component_id",
            "variation",
        ]

        for field in required_fields:
            if field not in metadata:
                errors.append(
                    {
                        "field": f"metadata.{field}",
                        "message": f"Missing '{field}' in metadata",
                        "severity": "error",
                    }
                )

        # Validate task_type
        if "task_type" in metadata and metadata["task_type"] not in TASK_TYPES:
            errors.append(
                {
                    "field": "metadata.task_type",
                    "message": f"Invalid task_type '{metadata['task_type']}'. Must be one of: {TASK_TYPES}",
                    "severity": "error",
                }
            )

        # Validate confidence
        if "confidence" in metadata:
            confidence = metadata["confidence"]
            if not isinstance(confidence, (int, float)):
                errors.append(
                    {
                        "field": "metadata.confidence",
                        "message": "Confidence must be a number",
                        "severity": "error",
                    }
                )
            elif confidence < 0.0 or confidence > 1.0:
                errors.append(
                    {
                        "field": "metadata.confidence",
                        "message": f"Confidence must be between 0.0 and 1.0, got {confidence}",
                        "severity": "error",
                    }
                )

        return errors

    def _check_patterns(self, question: str) -> list[dict]:
        """Check question against quality patterns.

        Args:
            question: Question text to check

        Returns:
            List of error dictionaries
        """
        errors = []

        # Check for empty role or directive
        if not question.strip() or re.match(r"^\s*[.]+\s*$", question):
            errors.append(
                {
                    "field": "question",
                    "message": "Question contains empty role or directive",
                    "severity": "error",
                }
            )

        # Check for framework mentions
        for framework in FRAMEWORKS:
            if framework.lower() in question.lower():
                errors.append(
                    {
                        "field": "question",
                        "message": f"Question contains framework mention: {framework}",
                        "severity": "error",
                    }
                )

        # Check for excessive special characters
        special_chars = re.findall(r'[^a-zA-Z0-9\s.,!?;:\-\'"()]', question)
        special_char_ratio = len(special_chars) / len(question) if question else 0

        if special_char_ratio > 0.3:
            errors.append(
                {
                    "field": "question",
                    "message": f"Question has too many special characters ({special_char_ratio:.2%})",
                    "severity": "error",
                }
            )

        # Check for balanced parentheses
        open_parens = question.count("(")
        close_parens = question.count(")")

        if open_parens != close_parens:
            errors.append(
                {
                    "field": "question",
                    "message": f"Unbalanced parentheses: {open_parens} open, {close_parens} close",
                    "severity": "error",
                }
            )

        # Check for repetition
        words = question.lower().split()
        word_counts = {}

        for word in words:
            if len(word) > 3:
                word_counts[word] = word_counts.get(word, 0) + 1

        repeated_words = [word for word, count in word_counts.items() if count > 3]

        if repeated_words:
            errors.append(
                {
                    "field": "question",
                    "message": f"Question contains repetition: {repeated_words}",
                    "severity": "error",
                }
            )

        return errors

    def _calculate_quality_score(
        self, example: dict, errors: list[dict], warnings: list[dict]
    ) -> float:
        """Calculate quality score for an example.

        Args:
            example: Example dictionary
            errors: List of errors
            warnings: List of warnings

        Returns:
            Quality score between 0.0 and 1.0
        """
        if "question" not in example:
            return 0.0

        question = example["question"]

        # Check for low character diversity (e.g., "x" * 60)
        unique_chars = len(set(question))
        total_chars = len(question)

        if total_chars > 0:
            char_diversity = unique_chars / total_chars
            # Only reject if extremely low diversity (single character repeated)
            if char_diversity < 0.05:
                return 0.2

        # Check for low lexical diversity
        words = question.split()
        unique_words = len(set(words))
        total_words = len(words)

        if total_words > 0:
            lexical_diversity = unique_words / total_words
            # More strict lexical diversity check
            if lexical_diversity < 0.2:
                return 0.3

        score = 0.5  # Base score

        # Length score
        ideal_length = 200
        length_score = min(1.0, len(question) / ideal_length)
        score += length_score * 0.2

        # Pattern bonuses
        # Check for context indicators
        context_keywords = [
            "explain",
            "describe",
            "analyze",
            "discuss",
            "provide",
            "example",
            "context",
            "background",
            "detail",
            "reasoning",
        ]
        context_count = sum(
            1 for keyword in context_keywords if keyword.lower() in question.lower()
        )
        score += min(0.15, context_count * 0.03)

        # Check for action verbs
        action_verbs = [
            "create",
            "build",
            "implement",
            "design",
            "develop",
            "write",
            "generate",
            "construct",
            "formulate",
        ]
        verb_count = sum(1 for verb in action_verbs if verb.lower() in question.lower())
        score += min(0.1, verb_count * 0.02)

        # Check for constraints
        constraint_keywords = [
            "constraint",
            "limit",
            "must",
            "should",
            "require",
            "within",
            "without",
            "except",
            "unless",
            "restrict",
        ]
        constraint_count = sum(
            1 for kw in constraint_keywords if kw.lower() in question.lower()
        )
        score += min(0.1, constraint_count * 0.02)

        # Metadata score
        if "metadata" in example:
            metadata = example["metadata"]

            # Confidence score
            if "confidence" in metadata:
                confidence = metadata["confidence"]
                score += confidence * 0.1

            # Task type bonus
            if "task_type" in metadata and metadata["task_type"] in TASK_TYPES:
                score += 0.05

        # Penalty for errors
        error_penalty = len(errors) * 0.2
        score -= error_penalty

        # Penalty for warnings
        warning_penalty = len(warnings) * 0.05
        score -= warning_penalty

        # Clamp score to [0.0, 1.0]
        return max(0.0, min(1.0, score))
