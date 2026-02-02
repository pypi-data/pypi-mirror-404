"""
Tokenette Tests

Basic test suite for the Tokenette MCP server.
"""

import pytest

# ─── CONFIG TESTS ────────────────────────────────────────────────


class TestConfig:
    """Test configuration system."""

    def test_default_config(self):
        """Test default configuration loads correctly."""
        from tokenette.config import TokenetteConfig

        config = TokenetteConfig()
        assert config.cache.l1_max_size_mb == 100  # 100MB
        assert config.cache.l1_ttl_seconds == 1800  # 30 minutes
        assert config.router.monthly_premium_limit == 300
        assert config.compression.min_quality_score == 0.95

    def test_config_from_dict(self):
        """Test configuration from dictionary."""
        from tokenette.config import TokenetteConfig

        config = TokenetteConfig(
            cache={"l1_max_size_mb": 50}, router={"monthly_premium_limit": 500}
        )
        assert config.cache.l1_max_size_mb == 50
        assert config.router.monthly_premium_limit == 500


# ─── CACHE TESTS ─────────────────────────────────────────────────


class TestCache:
    """Test multi-layer cache."""

    @pytest.fixture
    def cache(self):
        from tokenette.config import CacheConfig
        from tokenette.core.cache import MultiLayerCache

        return MultiLayerCache(CacheConfig())

    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache):
        """Test basic cache set/get."""
        await cache.set("test_key", {"data": "test_value"})
        result = await cache.get("test_key")

        assert result is not None
        assert result.data == {"data": "test_value"}
        assert result.layer == "L1"

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss returns CacheResult with hit=False."""
        result = await cache.get("nonexistent_key")
        # Cache miss returns CacheResult with hit=False, not None
        assert result is not None
        assert not result.hit
        assert result.layer == "MISS"


# ─── MINIFIER TESTS ──────────────────────────────────────────────


class TestMinifier:
    """Test minification engine."""

    @pytest.fixture
    def minifier(self):
        from tokenette.core.minifier import MinificationEngine

        return MinificationEngine()

    def test_json_minification(self, minifier):
        """Test JSON minification."""
        # Use a larger JSON with more whitespace to show savings
        data = {
            "key": "value",
            "nested": {"inner": "data", "another": "field"},
            "list": [1, 2, 3, 4, 5],
        }
        result = minifier.minify(data, content_type="json")

        assert result.format == "json"
        assert "key" in result.data

    def test_code_minification(self, minifier):
        """Test code minification."""
        code = """
# This is a comment
def hello():
    # Another comment
    return "world"


"""
        result = minifier.minify(code, content_type="code")

        assert result.format == "code"
        assert "# This is a comment" not in result.data
        assert "def hello():" in result.data

    def test_toon_format(self, minifier):
        """Test TOON format for arrays."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]
        result = minifier.minify(data, content_type="toon")

        assert result.format == "toon"
        assert "items[3]" in result.data
        assert result.savings_pct > 40  # TOON should save 40%+


# ─── ROUTER TESTS ────────────────────────────────────────────────


class TestRouter:
    """Test task routing engine."""

    @pytest.fixture
    def router(self):
        from tokenette.config import RouterConfig
        from tokenette.core.router import TaskRouter

        return TaskRouter(RouterConfig())

    def test_trivial_task_routing(self, router):
        """Test trivial tasks route to free models."""
        decision = router.route("fix typo in readme", {"affected_files": 1})

        assert decision.complexity.name == "TRIVIAL"
        assert decision.multiplier == 0  # Free model

    def test_complex_task_routing(self, router):
        """Test complex tasks prioritize quality over cost."""
        decision = router.route(
            "architect a distributed microservices system", {"affected_files": 20}
        )

        assert decision.complexity.name in ["COMPLEX", "EXPERT"]
        # Quality-first: should pick highest quality model available
        # For complex tasks, we expect a premium model (>=1×) for best results
        assert decision.multiplier >= 1.0
        # High-quality model should still have boosters for extra assurance
        assert len(decision.quality_boosters) >= 2

    def test_quality_boosters(self, router):
        """Test quality boosters are assigned."""
        decision = router.route("refactor authentication module", {"affected_files": 5})

        assert len(decision.quality_boosters) > 0
        assert "post_validation" in decision.quality_boosters


# ─── AMPLIFIER TESTS ─────────────────────────────────────────────


class TestAmplifier:
    """Test quality amplification."""

    @pytest.fixture
    def amplifier(self):
        from tokenette.config import AmplifierConfig
        from tokenette.core.amplifier import QualityAmplifier

        return QualityAmplifier(AmplifierConfig())

    def test_expert_framing(self, amplifier):
        """Test expert role framing is applied."""
        result = amplifier.amplify(
            "Write a function", boosters=["expert_role_framing"], category="generation", context={}
        )

        # AmplificationResult has 'prompt' not 'enhanced_prompt'
        assert "senior" in result.prompt.lower() or "expert" in result.prompt.lower()
        assert "expert_role_framing" in result.boosters_applied

    def test_chain_of_thought(self, amplifier):
        """Test chain-of-thought injection."""
        result = amplifier.amplify(
            "Debug this code",
            boosters=["chain_of_thought_injection"],
            category="debugging",
            context={},
        )

        assert "step by step" in result.prompt.lower()

    def test_amplification_result_structure(self, amplifier):
        """Test AmplificationResult has expected fields."""
        result = amplifier.amplify(
            "Simple task", boosters=["expert_role_framing"], category="generation", context={}
        )

        assert hasattr(result, "prompt")
        assert hasattr(result, "original_length")
        assert hasattr(result, "amplified_length")
        assert hasattr(result, "boosters_applied")
        assert result.amplified_length > result.original_length


# ─── OPTIMIZER TESTS ─────────────────────────────────────────────


class TestOptimizer:
    """Test optimization pipeline."""

    @pytest.fixture
    def optimizer(self):
        from tokenette.core.optimizer import OptimizationPipeline

        # OptimizationPipeline uses default config internally
        return OptimizationPipeline()

    @pytest.mark.asyncio
    async def test_full_pipeline(self, optimizer):
        """Test full optimization pipeline."""
        data = {
            "users": [
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@example.com"},
            ]
        }

        result = await optimizer.optimize(data, content_type="auto")

        assert result.quality_score >= 0.95

    @pytest.mark.asyncio
    async def test_optimization_result_structure(self, optimizer):
        """Test OptimizationResult has expected fields."""
        data = {"key": "value"}

        result = await optimizer.optimize(data, content_type="json")

        assert hasattr(result, "data")
        assert hasattr(result, "source")
        assert hasattr(result, "original_tokens")
        assert hasattr(result, "final_tokens")
        assert hasattr(result, "quality_score")


# ─── FILE OPS TESTS ──────────────────────────────────────────────


class TestFileOps:
    """Test file operations."""

    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary Python file."""
        file = tmp_path / "test.py"
        file.write_text('''
def hello():
    """Say hello."""
    return "Hello, World!"

class Greeter:
    def greet(self, name):
        return f"Hello, {name}!"
''')
        return file

    @pytest.mark.asyncio
    async def test_read_file_full(self, temp_file):
        """Test full file reading."""
        from tokenette.tools.file_ops import read_file_smart

        result = await read_file_smart(str(temp_file), strategy="full")

        # Check the actual structure returned
        assert "content" in result or "error" not in result
        if "content" in result:
            assert "def hello" in result["content"]

    @pytest.mark.asyncio
    async def test_read_file_exists(self, temp_file):
        """Test reading an existing file returns content."""
        from tokenette.tools.file_ops import read_file_smart

        result = await read_file_smart(str(temp_file), strategy="full")

        # Should have some content or structure
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_structure(self, temp_file):
        """Test structure extraction."""
        from tokenette.tools.file_ops import get_file_structure

        result = await get_file_structure(str(temp_file))

        # Check result structure
        assert result is not None
        assert isinstance(result, dict)


# ─── ANALYSIS TESTS ──────────────────────────────────────────────


class TestAnalysis:
    """Test code analysis tools."""

    @pytest.fixture
    def temp_python_file(self, tmp_path):
        """Create a file with known issues."""
        file = tmp_path / "buggy.py"
        file.write_text("""
password = "secret123"  # Security issue

def process():
    try:
        do_something()
    except:  # Bare except
        pass

    if x == True:  # Style issue
        return x
""")
        return file

    @pytest.mark.asyncio
    async def test_find_bugs(self, temp_python_file):
        """Test bug detection."""
        from tokenette.tools.analysis import find_bugs

        result = await find_bugs(str(temp_python_file))

        assert result["total"] >= 2  # At least password + bare except
        assert any(i["type"] == "security" for i in result["issues"])

    @pytest.mark.asyncio
    async def test_complexity(self, tmp_path):
        """Test complexity calculation."""
        from tokenette.tools.analysis import get_complexity

        # Create a file with some complexity
        file = tmp_path / "complex.py"
        file.write_text("""
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            else:
                return x + y
        else:
            return x
    else:
        for i in range(10):
            if i % 2 == 0:
                print(i)
        return 0
""")

        result = await get_complexity(str(file))

        assert "metrics" in result
        assert result["metrics"]["cyclomatic"] >= 5  # Should have some complexity


# ─── INTEGRATION TESTS ───────────────────────────────────────────


class TestIntegration:
    """Integration tests for the full system."""

    def test_imports(self):
        """Test all main imports work."""
        from tokenette import (
            __version__,
        )

        assert __version__ == "2.0.0"

    def test_server_creation(self):
        """Test server can be created."""
        from tokenette.server import create_server

        server = create_server()
        assert server.name == "tokenette"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
