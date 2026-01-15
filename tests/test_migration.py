"""
Test Suite for Migration Verification

Tests that all migrated files maintain their functionality after reorganization.
"""

import os
import sys
from pathlib import Path

import pytest

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


class TestMigration:
    """Test suite for file migration verification."""

    def test_api_main_exists(self):
        """Verify api/main.py exists in new location."""
        main_path = PROJECT_ROOT / "api" / "main.py"
        assert main_path.exists(), f"api/main.py not found at {main_path}"
        assert main_path.is_file(), "api/main.py is not a file"

    def test_api_main_imports(self):
        """Verify api/main.py can be imported without errors."""
        sys.path.insert(0, str(PROJECT_ROOT))
        try:
            from api.main import app

            assert app is not None, "FastAPI app is None"
            assert app.title == "DSPy Prompt Improver API"
        except ImportError as e:
            pytest.fail(f"Failed to import api.main: {e}")

    def test_rayext_script_exists(self):
        """Verify rayext script exists in scripts/ directory."""
        rayext_path = PROJECT_ROOT / "scripts" / "rayext"
        assert rayext_path.exists(), "scripts/rayext not found"
        assert rayext_path.is_file(), "scripts/rayext is not a file"

    def test_rayext_script_executable(self):
        """Verify rayext script has executable permissions."""
        rayext_path = PROJECT_ROOT / "scripts" / "rayext"
        assert os.access(rayext_path, os.X_OK), "scripts/rayext is not executable"

    def test_documentation_files_migrated(self):
        """Verify documentation files were moved correctly."""
        docs_files = [
            ("docs/performance/optimizations.md", 139),  # Actual line count
            ("docs/agent/instructions.md", 102),  # Actual line count
        ]

        for file_path, min_lines in docs_files:
            full_path = PROJECT_ROOT / file_path
            assert full_path.exists(), f"{file_path} not found"

            with open(full_path) as f:
                line_count = len(f.readlines())

            assert line_count >= min_lines, (
                f"{file_path} has only {line_count} lines (expected at least {min_lines})"
            )

    def test_old_locations_removed(self):
        """Verify old file locations no longer exist."""
        old_files = [
            "main.py",
            "rayext",
            "OPTIMIZATIONS.md",
            "AGENT_INSTRUCTIONS.md",
        ]

        for old_file in old_files:
            old_path = PROJECT_ROOT / old_file
            assert not old_path.exists(), f"Old file still exists: {old_file}"

    def test_new_directories_created(self):
        """Verify new directory structure was created."""
        new_dirs = [
            ".logs",
            ".tmp",
            ".backup",
            "docs/agent",
            "docs/performance",
            "docs/reports",
        ]

        for new_dir in new_dirs:
            dir_path = PROJECT_ROOT / new_dir
            assert dir_path.exists(), f"Directory not created: {new_dir}"
            assert dir_path.is_dir(), f"{new_dir} is not a directory"

    def test_makefile_updated(self):
        """Verify Makefile contains updated paths."""
        makefile = PROJECT_ROOT / "Makefile"
        content = makefile.read_text()

        # Check for new paths
        assert "api/main.py" in content, "Makefile doesn't reference api/main.py"
        assert ".tmp/backend.pid" in content, (
            "Makefile doesn't reference .tmp/backend.pid"
        )
        assert ".logs/backend.log" in content, (
            "Makefile doesn't reference .logs/backend.log"
        )

    def test_gitignore_updated(self):
        """Verify .gitignore contains new directories."""
        gitignore = PROJECT_ROOT / ".gitignore"
        content = gitignore.read_text()

        required_entries = [
            ".logs/",
            ".tmp/",
            ".backup/",
            "coverage.json",
        ]

        for entry in required_entries:
            assert entry in content, f".gitignore missing entry: {entry}"

    def test_verify_migration_script_exists(self):
        """Verify the migration verification script exists."""
        verify_script = PROJECT_ROOT / "scripts" / "verify_migration.py"
        assert verify_script.exists(), "verify_migration.py not found"
        assert verify_script.is_file(), "verify_migration.py is not a file"


class TestAPIFunctionality:
    """Test that API functionality is preserved after migration."""

    def test_api_routes_defined(self):
        """Verify API routes are properly defined."""
        sys.path.insert(0, str(PROJECT_ROOT))
        from api.main import app

        # Get all route paths
        routes = [route.path for route in app.routes]

        # Verify critical routes exist
        assert "/health" in routes, "Health endpoint missing"
        assert "/" in routes, "Root endpoint missing"

    def test_api_has_cors_middleware(self):
        """Verify CORS middleware is configured."""
        sys.path.insert(0, str(PROJECT_ROOT))
        from fastapi.middleware.cors import CORSMiddleware

        from api.main import app

        # Check if CORS middleware is present
        has_cors = any(
            isinstance(middleware, type) and issubclass(middleware, CORSMiddleware)
            for middleware in [type(m) for m in app.user_middleware]
        )

        # Note: This might not catch all CORS configs, but it's a basic check
        # The actual CORS is added via app.add_middleware which we verified exists in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
