"""Integration tests for DSPy few-shot learning with unified pool.

Tests the integration between:
1. Unified few-shot pool (datasets/exports/unified-fewshot-pool.json)
2. DSPy KNNFewShot optimizer
3. Feature flag (USE_KNN_FEWSHOT)
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import after adding to path
from eval.src.dspy_prompt_improver_fewshot import (
    PromptImproverWithFewShot,
    load_trainset,
    create_fewshot_improver,
)
from scripts.phase3_dspy.fewshot_optimizer import (
    load_unified_pool,
    compile_fewshot_with_pool,
    get_feature_flag,
)


class TestUnifiedPoolExists:
    """Test that unified pool exists and is ready for few-shot."""

    def test_unified_pool_exists(self):
        """Test that unified pool file exists."""
        pool_path = PROJECT_ROOT / 'datasets/exports/unified-fewshot-pool.json'
        assert pool_path.exists(), (
            "Unified pool not found at datasets/exports/unified-fewshot-pool.json. "
            "Run merge_unified_pool.py first!"
        )

    def test_unified_pool_structure(self):
        """Test that unified pool has correct structure."""
        pool_path = PROJECT_ROOT / 'datasets/exports/unified-fewshot-pool.json'

        if not pool_path.exists():
            pytest.skip("Unified pool not found")

        with open(pool_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check top-level structure
        assert 'metadata' in data
        assert 'examples' in data

        # Check metadata
        assert data['metadata']['total_examples'] >= 50
        assert len(data['examples']) >= 50

        # Check first example structure
        example = data['examples'][0]
        assert 'inputs' in example
        assert 'outputs' in example
        assert 'original_idea' in example['inputs']
        assert 'improved_prompt' in example['outputs']


class TestLoadUnifiedPool:
    """Test loading unified pool into DSPy Examples."""

    @pytest.fixture
    def pool_path(self):
        """Path to unified pool."""
        return PROJECT_ROOT / 'datasets/exports/unified-fewshot-pool.json'

    @pytest.fixture
    def trainset(self, pool_path):
        """Load trainset from unified pool."""
        if not pool_path.exists():
            pytest.skip("Unified pool not found")

        # Use the new load_unified_pool function
        return load_unified_pool(pool_path)

    def test_load_unified_pool_size(self, trainset):
        """Test that unified pool loads with expected size."""
        assert len(trainset) >= 50, f"Expected at least 50 examples, got {len(trainset)}"

    def test_load_unified_pool_structure(self, trainset):
        """Test that loaded examples have correct DSPy structure."""
        example = trainset[0]

        # Check that it's a DSPy Example
        import dspy
        assert isinstance(example, dspy.Example)

        # Check input fields
        assert hasattr(example, 'original_idea')
        assert hasattr(example, 'context')

        # Check output fields
        assert hasattr(example, 'improved_prompt')
        assert hasattr(example, 'role')
        assert hasattr(example, 'directive')
        assert hasattr(example, 'framework')

    def test_load_unified_pool_with_inputs(self, trainset):
        """Test that examples have proper inputs/outputs separation."""
        example = trainset[0]

        # DSPy Examples should have inputs() marked
        inputs = example.inputs()
        assert 'original_idea' in inputs
        assert 'context' in inputs


class TestFewshotOptimizer:
    """Test few-shot optimizer with unified pool."""

    @pytest.fixture
    def pool_path(self):
        """Path to unified pool."""
        path = PROJECT_ROOT / 'datasets/exports/unified-fewshot-pool.json'
        if not path.exists():
            pytest.skip("Unified pool not found")
        return path

    def test_create_fewshot_improver_with_unified_pool(self, pool_path, tmp_path):
        """Test creating few-shot improver with unified pool."""
        import dspy

        # Create improver using compile_fewshot_with_pool
        output_path = tmp_path / "compiled.json"
        improver = compile_fewshot_with_pool(
            trainset_path=pool_path,
            output_path=output_path,
            k=3
        )

        # Check that it compiled successfully
        assert improver._compiled is True
        assert improver.compiled_improver is not None
        assert improver.k == 3

        # Check metadata was saved
        assert output_path.exists()

    def test_fewshot_inference(self, pool_path, tmp_path):
        """Test few-shot inference with unified pool."""
        import dspy

        # Need to configure DSPy LM first
        try:
            from hemdov.infrastructure.config import Settings
            from hemdov.interfaces import container
            settings = container.get(Settings)

            # Try to configure DSPy with available LM
            if settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
                from hemdov.infrastructure.adapters.litellm_dspy_adapter_prompt import create_anthropic_adapter
                lm = create_anthropic_adapter(
                    model=settings.LLM_MODEL,
                    api_key=settings.ANTHROPIC_API_KEY,
                    temperature=0.0,
                )
                dspy.configure(lm=lm)
            else:
                pytest.skip("DSPy LM not configured")
        except Exception:
            pytest.skip("DSPy LM configuration failed")

        # Create improver
        output_path = tmp_path / "compiled.json"
        improver = compile_fewshot_with_pool(
            trainset_path=pool_path,
            output_path=output_path,
            k=3
        )

        # Test inference
        test_input = "Documenta una función TypeScript que calcula el factorial"

        result = improver(original_idea=test_input, context="")

        # Check result structure
        assert hasattr(result, 'improved_prompt')
        assert hasattr(result, 'role')
        assert hasattr(result, 'framework')

        # Check that we got a non-empty result
        assert len(result.improved_prompt) > 0
        assert len(result.role) > 0


class TestFeatureFlag:
    """Test USE_KNN_FEWSHOT feature flag."""

    def test_feature_flag_default_true(self):
        """Test that feature flag defaults to true."""
        # Clean environment
        if 'USE_KNN_FEWSHOT' in os.environ:
            del os.environ['USE_KNN_FEWSHOT']
        if 'DSPY_FEWSHOT_ENABLED' in os.environ:
            del os.environ['DSPY_FEWSHOT_ENABLED']

        # get_feature_flag() defaults to True
        assert get_feature_flag() is True

    def test_feature_flag_can_disable_fewshot(self):
        """Test that fewshot can be disabled via environment variable."""
        # Set feature flag to false
        os.environ['USE_KNN_FEWSHOT'] = 'false'

        try:
            assert get_feature_flag() is False
        finally:
            # Clean up
            if 'USE_KNN_FEWSHOT' in os.environ:
                del os.environ['USE_KNN_FEWSHOT']

    def test_feature_flag_can_enable_fewshot(self):
        """Test that fewshot can be enabled via environment variable."""
        # Set feature flag to true
        os.environ['USE_KNN_FEWSHOT'] = 'true'

        try:
            assert get_feature_flag() is True
        finally:
            # Clean up
            if 'USE_KNN_FEWSHOT' in os.environ:
                del os.environ['USE_KNN_FEWSHOT']

    def test_feature_alias_use_knn_fewshot(self):
        """Test that USE_KNN_FEWSHOT takes precedence."""
        # Set both flags
        os.environ['USE_KNN_FEWSHOT'] = 'true'
        os.environ['DSPY_FEWSHOT_ENABLED'] = 'false'

        try:
            # USE_KNN_FEWSHOT should take precedence
            assert get_feature_flag() is True
        finally:
            # Clean up
            if 'USE_KNN_FEWSHOT' in os.environ:
                del os.environ['USE_KNN_FEWSHOT']
            if 'DSPY_FEWSHOT_ENABLED' in os.environ:
                del os.environ['DSPY_FEWSHOT_ENABLED']

    def test_feature_fallback_to_dspy_fewshot_enabled(self):
        """Test fallback to DSPY_FEWSHOT_ENABLED when USE_KNN_FEWSHOT not set."""
        # Set only legacy flag
        os.environ['DSPY_FEWSHOT_ENABLED'] = 'true'

        try:
            assert get_feature_flag() is True
        finally:
            # Clean up
            if 'DSPY_FEWSHOT_ENABLED' in os.environ:
                del os.environ['DSPY_FEWSHOT_ENABLED']


class TestCompiledMetadata:
    """Test compiled metadata for few-shot optimizer."""

    def test_compiled_metadata_structure(self):
        """Test that compiled metadata has expected structure."""
        metadata_path = PROJECT_ROOT / 'models/prompt_improver_fewshot.metadata.json'

        if not metadata_path.exists():
            pytest.skip("Compiled metadata not found")

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        # Check structure
        assert 'compiled' in metadata
        assert 'k' in metadata
        assert 'trainset_size' in metadata

        # Check values
        assert isinstance(metadata['k'], int)
        assert metadata['k'] > 0
        assert isinstance(metadata['trainset_size'], int)
        assert metadata['trainset_size'] > 0
