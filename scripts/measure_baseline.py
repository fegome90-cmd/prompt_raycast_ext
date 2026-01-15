#!/usr/bin/env python3
"""Measure baseline metrics before NLaC pipeline changes.

This script measures the current baseline performance and code quality
before implementing the NLaC Pipeline v3.0 improvements.
"""
import json
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hemdov.domain.services.knn_provider import KNNProvider


class BaselineMeasurer:
    """Measures baseline metrics for the codebase."""

    def __init__(self, output_path: Path = Path("data/baseline-v3.0.json")):
        """
        Initialize baseline measurer.

        Args:
            output_path: Path to save baseline results
        """
        self.output_path = output_path
        self.results: dict[str, Any] = {}

    def measure_knn_latency(self, iterations: int = 100) -> dict[str, float]:
        """
        Measure KNN provider latency.

        Args:
            iterations: Number of measurements to take

        Returns:
            Dict with p50, p95, p99, mean, min, max latency values
        """
        knn = KNNProvider(catalog_path=Path("datasets/exports/unified-fewshot-pool-v2.json"))

        latencies = []
        for _ in range(iterations):
            start = time.perf_counter()
            examples = knn.find_examples(
                intent="explain",
                complexity="moderate",
                k=3
            )
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        return {
            "p50": statistics.median(latencies),
            "p95": sorted(latencies)[int(iterations * 0.95)],
            "p99": sorted(latencies)[int(iterations * 0.99)],
            "mean": statistics.mean(latencies),
            "min": min(latencies),
            "max": max(latencies),
        }

    def measure_exception_coverage(self) -> dict[str, Any]:
        """
        Count specific vs generic exceptions in domain services.

        Returns:
            Dict with coverage percentage and counts
        """
        from glob import glob

        services = glob("hemdov/domain/services/*.py")
        specific_count = 0
        generic_count = 0

        for service in services:
            content = Path(service).read_text()

            # Count specific exceptions
            specific_count += len(re.findall(
                r'except\s*\((?:RuntimeError|KeyError|TypeError|ValueError|ConnectionError|TimeoutError)',
                content
            ))

            # Count generic exceptions (anti-pattern)
            generic_count += len(re.findall(
                r'except\s*Exception\s*:',
                content
            ))

        total = specific_count + generic_count
        if total == 0:
            return {
                "coverage": "100%",
                "coverage_decimal": 1.0,
                "specific": specific_count,
                "generic": generic_count
            }

        return {
            "coverage": f"{(specific_count / total) * 100:.1f}%",
            "coverage_decimal": specific_count / total,
            "specific": specific_count,
            "generic": generic_count
        }

    def measure_catalog_stats(self) -> dict[str, Any]:
        """
        Measure catalog statistics.

        Returns:
            Dict with catalog size and metadata
        """
        catalog_path = Path("datasets/exports/unified-fewshot-pool-v2.json")

        if not catalog_path.exists():
            return {
                "error": "Catalog not found",
                "path": str(catalog_path)
            }

        with open(catalog_path) as f:
            catalog_data = json.load(f)

        examples = catalog_data.get("examples", [])

        # Count by intent
        intents = {}
        complexities = {}

        for ex in examples:
            # Count intents
            intent = ex.get("inputs", {}).get("original_idea", "")
            if "explain" in intent.lower():
                intents["explain"] = intents.get("explain", 0) + 1
            elif "create" in intent.lower() or "implement" in intent.lower():
                intents["create/implement"] = intents.get("create/implement", 0) + 1
            else:
                intents["other"] = intents.get("other", 0) + 1

            # Count complexities
            complexity = ex.get("inputs", {}).get("complexity", "unknown")
            complexities[complexity] = complexities.get(complexity, 0) + 1

        return {
            "total_examples": len(examples),
            "intents": intents,
            "complexities": complexities,
            "catalog_path": str(catalog_path)
        }

    def run_all(self) -> None:
        """Run all baseline measurements."""
        print("=" * 60)
        print("🔍 Baseline Measurement (v3.0)")
        print("=" * 60)

        print("\n  Measuring KNN latency (100 iterations)...")
        try:
            self.results["knn_latency"] = self.measure_knn_latency(100)
        except Exception as e:
            print(f"    ⚠️  KNN latency measurement failed: {e}")
            self.results["knn_latency"] = {"error": str(e)}

        print("\n  Measuring exception coverage...")
        try:
            self.results["exception_coverage"] = self.measure_exception_coverage()
        except Exception as e:
            print(f"    ⚠️  Exception coverage measurement failed: {e}")
            self.results["exception_coverage"] = {"error": str(e)}

        print("\n  Measuring catalog statistics...")
        try:
            self.results["catalog_stats"] = self.measure_catalog_stats()
        except Exception as e:
            print(f"    ⚠️  Catalog statistics measurement failed: {e}")
            self.results["catalog_stats"] = {"error": str(e)}

        # Save results
        self.output_path.parent.mkdir(exist_ok=True)
        with open(self.output_path, "w") as f:
            json.dump({
                "timestamp": time.time(),
                "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
                "results": self.results
            }, f, indent=2)

        print(f"\n💾 Baseline saved to {self.output_path}")
        self._print_summary()

    def _print_summary(self) -> None:
        """Print baseline summary."""
        print("\n" + "=" * 60)
        print("📊 Baseline Summary")
        print("=" * 60)

        # KNN Latency
        if "error" not in self.results.get("knn_latency", {}):
            knn = self.results["knn_latency"]
            print("\n  KNN Latency (100 iterations):")
            print(f"    P50:  {knn['p50']:.2f}ms")
            print(f"    P95:  {knn['p95']:.2f}ms")
            print(f"    P99:  {knn['p99']:.2f}ms")
            print(f"    Mean: {knn['mean']:.2f}ms")
            print(f"    Min:  {knn['min']:.2f}ms")
            print(f"    Max:  {knn['max']:.2f}ms")

        # Exception Coverage
        if "error" not in self.results.get("exception_coverage", {}):
            exc = self.results["exception_coverage"]
            print("\n  Exception Coverage:")
            print(f"    Coverage: {exc['coverage']}")
            print(f"    Specific: {exc['specific']}")
            print(f"    Generic:  {exc['generic']}")

        # Catalog Stats
        if "error" not in self.results.get("catalog_stats", {}):
            cat = self.results["catalog_stats"]
            print("\n  Catalog Statistics:")
            print(f"    Total Examples: {cat['total_examples']}")
            print(f"    Intents: {cat['intents']}")
            print(f"    Complexities: {cat['complexities']}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        BaselineMeasurer().run_all()
        print("\n✅ Baseline measurement complete!")
    except Exception as e:
        print(f"\n❌ Baseline measurement failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
