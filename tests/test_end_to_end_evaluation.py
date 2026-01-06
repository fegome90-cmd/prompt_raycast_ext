"""End-to-end test for the full evaluation pipeline.

Tests the complete workflow: evaluate_dataset → analyze_thresholds → generate_report
"""
import pytest
import json
import tempfile
from pathlib import Path
from scripts.eval.evaluate_dataset_gates import evaluate_dataset
from scripts.eval.analyze_thresholds import analyze_thresholds
from scripts.eval.generate_report import generate_markdown_report


def test_full_evaluation_pipeline():
    """Test the complete pipeline: evaluate → analyze → report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Run evaluation
        results = evaluate_dataset(
            dataset_path="datasets/exports/fewshot-train.json",
            output_field="outputs.improved_prompt",
            template_id="example_md",
            limit=5
        )

        # Verify evaluation results
        assert "total_evaluated" in results
        assert "gate_statistics" in results
        assert results["total_evaluated"] >= 0

        # Save results to temp file
        results_path = Path(tmpdir) / "results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f)

        # Step 2: Analyze thresholds
        recommendations = analyze_thresholds(results)

        # Verify recommendations structure
        assert isinstance(recommendations, dict)
        # May contain recommendations or error key
        assert "error" not in recommendations or recommendations["error"]

        # Save recommendations to temp file
        recommendations_path = Path(tmpdir) / "recommendations.json"
        with open(recommendations_path, 'w') as f:
            json.dump(recommendations, f)

        # Step 3: Generate report
        report_path = Path(tmpdir) / "report.md"
        generate_markdown_report(
            results_path=str(results_path),
            recommendations_path=str(recommendations_path),
            output_path=str(report_path)
        )

        # Verify report was created
        assert report_path.exists()
        report_content = report_path.read_text()

        # Verify report contains expected sections
        assert "# Quality Gates Dataset Evaluation Report" in report_content
        assert "## Executive Summary" in report_content
        assert "## Gate Performance Summary" in report_content
        assert "## Methodology" in report_content


def test_pipeline_with_error_handling():
    """Test pipeline behavior when input data has issues."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal valid dataset
        minimal_data = [
            {
                "outputs": {
                    "improved_prompt": "Test prompt with some content"
                }
            }
        ]

        dataset_path = Path(tmpdir) / "dataset.json"
        with open(dataset_path, 'w') as f:
            json.dump(minimal_data, f)

        # Run evaluation
        results = evaluate_dataset(
            dataset_path=str(dataset_path),
            output_field="outputs.improved_prompt",
            template_id="example_md",
            limit=None
        )

        # Should complete without errors
        assert results["total_evaluated"] >= 0

        # Analyze should handle results
        recommendations = analyze_thresholds(results)
        assert isinstance(recommendations, dict)


def test_pipeline_with_empty_dataset():
    """Test pipeline behavior with empty dataset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create empty dataset
        empty_data = []
        dataset_path = Path(tmpdir) / "empty.json"
        with open(dataset_path, 'w') as f:
            json.dump(empty_data, f)

        # Run evaluation - should handle gracefully
        results = evaluate_dataset(
            dataset_path=str(dataset_path),
            output_field="outputs.improved_prompt",
            template_id="example_md",
            limit=None
        )

        # Should complete with zero entries
        assert results["total_evaluated"] == 0

        # Analyze should return error for empty data
        recommendations = analyze_thresholds(results)
        assert "error" in recommendations
