#!/usr/bin/env python3
"""
Migration Verification Script

Tests that all file relocations were successful and path references are correct.
Run after completing the root directory reorganization.
"""

import os
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.parent


class MigrationVerifier:
    """Verify file migration and path references."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def check_file_exists(self, path: Path, description: str) -> bool:
        """Check if a file exists at the expected location."""
        if path.exists():
            print(f"{GREEN}✓{RESET} {description}: {path.relative_to(PROJECT_ROOT)}")
            self.passed += 1
            return True
        else:
            print(
                f"{RED}✗{RESET} {description}: {path.relative_to(PROJECT_ROOT)} NOT FOUND"
            )
            self.failed += 1
            return False

    def check_file_not_exists(self, path: Path, description: str) -> bool:
        """Check that a file was successfully moved (no longer in old location)."""
        if not path.exists():
            print(
                f"{GREEN}✓{RESET} {description}: {path.relative_to(PROJECT_ROOT)} (correctly removed)"
            )
            self.passed += 1
            return True
        else:
            print(
                f"{YELLOW}⚠{RESET} {description}: {path.relative_to(PROJECT_ROOT)} still exists"
            )
            self.warnings += 1
            return False

    def check_path_in_file(
        self, file_path: Path, search_term: str, description: str
    ) -> bool:
        """Check if a file contains expected path references."""
        if not file_path.exists():
            print(
                f"{YELLOW}⚠{RESET} {description}: {file_path.relative_to(PROJECT_ROOT)} not found to check"
            )
            self.warnings += 1
            return False

        try:
            content = file_path.read_text()
            if search_term in content:
                print(
                    f"{GREEN}✓{RESET} {description}: Found '{search_term}' in {file_path.name}"
                )
                self.passed += 1
                return True
            else:
                print(
                    f"{RED}✗{RESET} {description}: '{search_term}' NOT found in {file_path.name}"
                )
                self.failed += 1
                return False
        except Exception as e:
            print(f"{RED}✗{RESET} {description}: Error reading {file_path.name}: {e}")
            self.failed += 1
            return False

    def verify_directory_structure(self):
        """Verify new directory structure exists."""
        print("\n" + "=" * 60)
        print("Phase 1: Directory Structure")
        print("=" * 60)

        directories = [
            (PROJECT_ROOT / ".logs", "Logs directory"),
            (PROJECT_ROOT / ".tmp", "Temporary files directory"),
            (PROJECT_ROOT / ".backup", "Backup directory"),
            (PROJECT_ROOT / "docs" / "agent", "Agent docs directory"),
            (PROJECT_ROOT / "docs" / "performance", "Performance docs directory"),
            (PROJECT_ROOT / "docs" / "reports", "Reports directory"),
        ]

        for dir_path, description in directories:
            self.check_file_exists(dir_path, description)

    def verify_documentation_migration(self):
        """Verify documentation files were moved correctly."""
        print("\n" + "=" * 60)
        print("Phase 2: Documentation Files")
        print("=" * 60)

        # Check new locations
        self.check_file_exists(
            PROJECT_ROOT / "docs" / "performance" / "optimizations.md",
            "Optimizations docs (new location)",
        )
        self.check_file_exists(
            PROJECT_ROOT / "docs" / "agent" / "instructions.md",
            "Agent instructions (new location)",
        )

        # Check old locations removed
        self.check_file_not_exists(
            PROJECT_ROOT / "OPTIMIZATIONS.md", "OPTIMIZATIONS.md (old location)"
        )
        self.check_file_not_exists(
            PROJECT_ROOT / "AGENT_INSTRUCTIONS.md",
            "AGENT_INSTRUCTIONS.md (old location)",
        )

    def verify_temporary_files_migration(self):
        """Verify temporary/generated files were moved."""
        print("\n" + "=" * 60)
        print("Phase 3: Temporary & Generated Files")
        print("=" * 60)

        # Check new locations
        temp_files = [
            (".tmp/coverage.json", "Coverage report"),
            (".logs/backend.log", "Backend log"),
            (".tmp/backend.pid", "Backend PID file"),
        ]

        for rel_path, description in temp_files:
            # These files may not exist if not generated yet, so just check directory
            path = PROJECT_ROOT / rel_path
            if path.exists():
                self.check_file_exists(path, description)
            else:
                print(
                    f"{YELLOW}⚠{RESET} {description}: {rel_path} (not generated yet - OK)"
                )
                self.warnings += 1

        # Check code-review-results in reports
        reports_dir = PROJECT_ROOT / "docs" / "reports"
        if reports_dir.exists():
            review_files = list(reports_dir.glob("code-review-*.json"))
            if review_files:
                print(f"{GREEN}✓{RESET} Code review results in docs/reports/")
                self.passed += 1
            else:
                print(f"{YELLOW}⚠{RESET} No code-review-*.json files in docs/reports/")
                self.warnings += 1

        # Check old locations removed
        self.check_file_not_exists(
            PROJECT_ROOT / "coverage.json", "coverage.json (old location)"
        )
        self.check_file_not_exists(
            PROJECT_ROOT / ".backend.log", ".backend.log (old location)"
        )
        self.check_file_not_exists(
            PROJECT_ROOT / ".backend.pid", ".backend.pid (old location)"
        )

    def verify_backup_migration(self):
        """Verify backup files were moved."""
        print("\n" + "=" * 60)
        print("Phase 4: Backup Files")
        print("=" * 60)

        backup_dir = PROJECT_ROOT / ".backup"
        if backup_dir.exists():
            env_backups = list(backup_dir.glob("env.backup.ollama*"))
            if env_backups:
                print(f"{GREEN}✓{RESET} Env backup in .backup/")
                self.passed += 1
            else:
                print(f"{YELLOW}⚠{RESET} No env.backup.ollama* in .backup/")
                self.warnings += 1

        self.check_file_not_exists(
            PROJECT_ROOT / ".env.backup.ollama", ".env.backup.ollama (old location)"
        )

    def verify_scripts_migration(self):
        """Verify critical scripts were moved and references updated."""
        print("\n" + "=" * 60)
        print("Phase 5: Scripts & Entrypoints")
        print("=" * 60)

        # Check rayext
        rayext_new = PROJECT_ROOT / "scripts" / "rayext"
        if self.check_file_exists(rayext_new, "rayext script (new location)"):
            # Check if executable
            if os.access(rayext_new, os.X_OK):
                print(f"{GREEN}✓{RESET} rayext is executable")
                self.passed += 1
            else:
                print(f"{RED}✗{RESET} rayext is NOT executable")
                self.failed += 1

        # Check main.py
        self.check_file_exists(
            PROJECT_ROOT / "api" / "main.py", "main.py (new location in api/)"
        )

        # Check old locations
        self.check_file_not_exists(PROJECT_ROOT / "rayext", "rayext (old location)")
        self.check_file_not_exists(PROJECT_ROOT / "main.py", "main.py (old location)")

    def verify_path_references(self):
        """Verify path references were updated in config files."""
        print("\n" + "=" * 60)
        print("Phase 6: Path References")
        print("=" * 60)

        # Check Makefile references
        makefile = PROJECT_ROOT / "Makefile"
        if makefile.exists():
            self.check_path_in_file(
                makefile, "api/main.py", "Makefile references api/main.py"
            )

        # Check README references
        readme = PROJECT_ROOT / "README.md"
        if readme.exists():
            # Just verify README exists, specific content check might vary
            print(f"{GREEN}✓{RESET} README.md exists for manual review")
            self.passed += 1

    def verify_gitignore(self):
        """Verify .gitignore was updated."""
        print("\n" + "=" * 60)
        print("Phase 7: .gitignore Updates")
        print("=" * 60)

        gitignore = PROJECT_ROOT / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()

            checks = [
                (".logs/", ".logs/ directory"),
                (".tmp/", ".tmp/ directory"),
                (".backup/", ".backup/ directory"),
                ("coverage.json", "coverage.json file"),
            ]

            for pattern, description in checks:
                if pattern in content:
                    print(f"{GREEN}✓{RESET} .gitignore contains {description}")
                    self.passed += 1
                else:
                    print(f"{YELLOW}⚠{RESET} .gitignore missing {description}")
                    self.warnings += 1

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("MIGRATION VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"{GREEN}Passed:{RESET} {self.passed}")
        print(f"{RED}Failed:{RESET} {self.failed}")
        print(f"{YELLOW}Warnings:{RESET} {self.warnings}")
        print("=" * 60)

        if self.failed > 0:
            print(f"\n{RED}❌ Migration verification FAILED{RESET}")
            print(f"Please review the {self.failed} failed check(s) above.")
            return False
        elif self.warnings > 0:
            print(
                f"\n{YELLOW}⚠ Migration completed with {self.warnings} warning(s){RESET}"
            )
            print("Review warnings to ensure everything is as expected.")
            return True
        else:
            print(f"\n{GREEN}✅ Migration verification PASSED{RESET}")
            print("All files successfully migrated and references updated!")
            return True


def main():
    """Run migration verification."""
    print(f"\n{'=' * 60}")
    print("ROOT DIRECTORY MIGRATION VERIFICATION")
    print(f"{'=' * 60}\n")
    print(f"Project Root: {PROJECT_ROOT}\n")

    verifier = MigrationVerifier()

    # Run all verification phases
    verifier.verify_directory_structure()
    verifier.verify_documentation_migration()
    verifier.verify_temporary_files_migration()
    verifier.verify_backup_migration()
    verifier.verify_scripts_migration()
    verifier.verify_path_references()
    verifier.verify_gitignore()

    # Print summary
    success = verifier.print_summary()

    # Exit with appropriate code
    sys.exit(0 if success and verifier.failed == 0 else 1)


if __name__ == "__main__":
    main()
