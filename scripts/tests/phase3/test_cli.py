"""Tests for CLI entry point."""
from pathlib import Path


def test_cli_main_command():
    """Should have main command entry point"""
    import sys
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "scripts.phase3_pipeline.main"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent.parent
    )

    assert result.returncode == 0, f"CLI failed with: {result.stderr}"
    output = result.stdout
    assert "Optimization complete" in output, f"Expected 'Optimization complete' in output, got: {output}"
    assert "Train size: 11" in output, f"Expected train size in output, got: {output}"
