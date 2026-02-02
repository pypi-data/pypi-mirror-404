"""
Tokenette - The Ultimate All-in-One AI Coding Enhancement MCP

Zero-Loss Token Optimization · Intelligent Model Routing · Quality Amplification

Tokenette achieves 90-99% token reduction without sacrificing code quality through:
- Intelligent multi-layer caching (L1-L4)
- Semantic compression with quality preservation
- Dynamic tool discovery (96% reduction vs. static tools)
- Smart file operations with AST analysis
- Context7 integration for documentation

Example:
    >>> from tokenette import mcp
    >>> mcp.run()

For CLI usage:
    $ tokenette run
    $ tokenette metrics
    $ tokenette config
"""

from tokenette.config import TokenetteConfig, get_config
from tokenette.core.amplifier import QualityAmplifier
from tokenette.core.cache import MultiLayerCache
from tokenette.core.compressor import SemanticCompressor
from tokenette.core.minifier import MinificationEngine
from tokenette.core.optimizer import OptimizationPipeline
from tokenette.core.router import Complexity, TaskCategory, TaskRouter


# Lazy import to avoid circular dependencies
def _get_server():
    from tokenette.server import create_server, mcp

    return mcp, create_server


__version__ = "2.0.0"
__author__ = "Adarsh"
__license__ = "MIT"

__all__ = [
    # Server
    "mcp",
    "create_server",
    # Core components
    "MultiLayerCache",
    "MinificationEngine",
    "SemanticCompressor",
    "OptimizationPipeline",
    "TaskRouter",
    "Complexity",
    "TaskCategory",
    "QualityAmplifier",
    # Config
    "TokenetteConfig",
    "get_config",
    # Metadata
    "__version__",
]


# Lazy loading for server
def __getattr__(name):
    if name in ("mcp", "create_server"):
        mcp, create_server = _get_server()
        globals()["mcp"] = mcp
        globals()["create_server"] = create_server
        return mcp if name == "mcp" else create_server
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
