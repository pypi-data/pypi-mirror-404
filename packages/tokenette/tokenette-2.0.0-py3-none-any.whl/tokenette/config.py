"""
Tokenette Configuration System

Provides flexible configuration for all Tokenette components including:
- Cache settings (TTL, size limits, layers)
- Compression thresholds
- Model routing preferences
- Context7 integration settings
- Metrics and logging
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class CacheConfig(BaseModel):
    """Multi-layer cache configuration."""

    # L1: Hot cache (in-memory LRU)
    l1_enabled: bool = True
    l1_max_size_mb: int = 100
    l1_ttl_seconds: int = 1800  # 30 minutes

    # L2: Warm cache (disk-based)
    l2_enabled: bool = True
    l2_max_size_mb: int = 2048  # 2GB
    l2_ttl_seconds: int = 14400  # 4 hours
    l2_directory: Path = Field(default_factory=lambda: Path.home() / ".cache" / "tokenette" / "l2")

    # L3: Cold storage
    l3_enabled: bool = True
    l3_max_size_mb: int = 51200  # 50GB
    l3_ttl_seconds: int = 604800  # 7 days
    l3_directory: Path = Field(default_factory=lambda: Path.home() / ".cache" / "tokenette" / "l3")

    # L4: Semantic index (vector-based)
    l4_enabled: bool = False  # Requires vector dependencies
    l4_ttl_seconds: int = 2592000  # 30 days
    l4_similarity_threshold: float = 0.92


class CompressionConfig(BaseModel):
    """Compression and minification settings."""

    # Quality thresholds
    min_quality_score: float = 0.95  # Never compress below this similarity
    max_compression_ratio: float = 0.99  # Maximum allowed compression

    # Minification
    minify_json: bool = True
    minify_code: bool = True
    use_toon_format: bool = True  # Use TOON for homogeneous arrays
    toon_min_items: int = 10  # Min items for TOON format

    # Large text handling
    large_text_threshold: int = 4000  # Characters
    stream_large_responses: bool = True

    # Deduplication
    deduplicate_enabled: bool = True
    reference_extraction_enabled: bool = True
    min_ref_size: int = 100  # Only create refs for objects > 100 chars


class RouterConfig(BaseModel):
    """Task routing and model selection settings."""

    # Monthly budget
    monthly_premium_limit: int = 300

    # Auto-mode discount (10% off for auto routing)
    use_auto_mode_discount: bool = True
    auto_mode_discount_rate: float = 0.10

    # Quality thresholds per complexity level
    trivial_quality_threshold: float = 0.80
    simple_quality_threshold: float = 0.80
    moderate_quality_threshold: float = 0.85
    complex_quality_threshold: float = 0.90
    expert_quality_threshold: float = 0.95

    # Learning
    adaptive_learning_enabled: bool = True
    min_samples_for_learning: int = 5


class AmplifierConfig(BaseModel):
    """Quality amplification settings."""

    use_role_framing: bool = True
    use_chain_of_thought: bool = True
    use_few_shot_examples: bool = True
    use_structured_output: bool = True
    use_tradeoff_analysis: bool = True
    post_validation_enabled: bool = True


class Context7Config(BaseModel):
    """Context7 documentation integration settings."""

    enabled: bool = True
    api_base_url: str = "https://context7.dev/api"
    cache_docs: bool = True
    doc_cache_ttl_seconds: int = 86400  # 24 hours
    max_doc_tokens: int = 8000  # Max tokens per doc fetch
    auto_detect_packages: bool = True
    compress_docs: bool = True


class MetricsConfig(BaseModel):
    """Metrics and observability settings."""

    enabled: bool = True
    track_token_savings: bool = True
    track_cache_hits: bool = True
    track_compression_ratios: bool = True
    track_model_usage: bool = True
    persist_metrics: bool = True
    metrics_file: Path = Field(
        default_factory=lambda: Path.home() / ".cache" / "tokenette" / "metrics.json"
    )


class ServerConfig(BaseModel):
    """MCP Server settings."""

    name: str = "Tokenette"
    version: str = "2.0.0"
    transport: Literal["stdio", "sse", "http"] = "stdio"
    host: str = "127.0.0.1"
    port: int = 8765
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Tool settings
    lazy_load_tools: bool = True
    meta_tools_only: bool = False  # Only expose meta tools (discover, get_details, execute)


class TokenetteConfig(BaseSettings):
    """
    Main Tokenette configuration.

    Configuration can be set via:
    1. Environment variables (TOKENETTE_*)
    2. .tokenette.json config file
    3. Direct instantiation

    Example:
        >>> config = TokenetteConfig(
        ...     cache=CacheConfig(l1_max_size_mb=200),
        ...     server=ServerConfig(log_level="DEBUG")
        ... )
    """

    model_config = {"env_prefix": "TOKENETTE_", "env_nested_delimiter": "__"}

    # Component configs
    cache: CacheConfig = Field(default_factory=CacheConfig)
    compression: CompressionConfig = Field(default_factory=CompressionConfig)
    router: RouterConfig = Field(default_factory=RouterConfig)
    amplifier: AmplifierConfig = Field(default_factory=AmplifierConfig)
    context7: Context7Config = Field(default_factory=Context7Config)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)

    @classmethod
    def from_file(cls, path: Path | str) -> TokenetteConfig:
        """Load configuration from a JSON file."""
        import json

        path = Path(path)
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            return cls(**data)
        return cls()

    @classmethod
    def auto_discover(cls) -> TokenetteConfig:
        """
        Auto-discover configuration from common locations:
        1. .tokenette.json in current directory
        2. .tokenette.json in home directory
        3. Environment variables
        4. Default values
        """
        # Check current directory
        local_config = Path.cwd() / ".tokenette.json"
        if local_config.exists():
            return cls.from_file(local_config)

        # Check home directory
        home_config = Path.home() / ".tokenette.json"
        if home_config.exists():
            return cls.from_file(home_config)

        # Fall back to env vars and defaults
        return cls()

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return self.model_dump()

    def save(self, path: Path | str) -> None:
        """Save configuration to a JSON file."""
        import json

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.model_dump(), f, indent=2, default=str)


# Default configuration instance
_config: TokenetteConfig | None = None


def get_config() -> TokenetteConfig:
    """
    Get the global configuration instance.

    Auto-discovers configuration from:
    1. .tokenette.json in current directory
    2. .tokenette.json in home directory
    3. Environment variables (TOKENETTE_*)
    4. Default values

    Returns:
        TokenetteConfig: The configuration instance
    """
    global _config
    if _config is None:
        _config = TokenetteConfig.auto_discover()
    return _config


def set_config(config: TokenetteConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration to trigger re-discovery."""
    global _config
    _config = None


# Backwards compatibility
default_config = TokenetteConfig()
