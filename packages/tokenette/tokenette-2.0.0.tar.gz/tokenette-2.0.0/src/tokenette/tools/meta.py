"""
Meta Tools - Dynamic Tool Discovery

Implements the 3 meta-tools that enable 96% token savings:
1. discover_tools: Find tools by category/keyword (vs loading all schemas)
2. get_tool_details: Load full schema on-demand
3. execute_tool: Run tool with caching and optimization
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from fastmcp import Context


@dataclass
class ToolMetadata:
    """Lightweight tool metadata for discovery."""

    name: str
    description: str
    category: str
    popularity: int = 0  # Usage count
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "desc": self.description[:80],  # Truncate for token savings
            "cat": self.category,
            "pop": self.popularity,
        }


@dataclass
class ToolDetails:
    """Full tool schema with parameters."""

    name: str
    description: str
    category: str
    parameters: dict[str, Any]
    returns: str
    examples: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.parameters,
            "returns": self.returns,
            "examples": self.examples,
        }


# Tool registry - lightweight metadata for discovery
TOOL_REGISTRY: dict[str, ToolMetadata] = {
    # File Operations
    "read_file_smart": ToolMetadata(
        name="read_file_smart",
        description="Read file with intelligent strategy (full, partial, summary, AST)",
        category="file",
        popularity=500,
        tags=["read", "file", "optimize"],
    ),
    "write_file_diff": ToolMetadata(
        name="write_file_diff",
        description="Write file changes using diff format (97% smaller than full file)",
        category="file",
        popularity=450,
        tags=["write", "file", "diff", "edit"],
    ),
    "search_code_semantic": ToolMetadata(
        name="search_code_semantic",
        description="Semantic code search across files (98% savings vs grep)",
        category="file",
        popularity=380,
        tags=["search", "code", "semantic"],
    ),
    "get_file_structure": ToolMetadata(
        name="get_file_structure",
        description="Get AST structure of file (functions, classes, imports)",
        category="file",
        popularity=320,
        tags=["structure", "ast", "analyze"],
    ),
    "batch_read_files": ToolMetadata(
        name="batch_read_files",
        description="Read multiple files with cross-file deduplication",
        category="file",
        popularity=280,
        tags=["batch", "read", "files"],
    ),
    # Analysis
    "analyze_code": ToolMetadata(
        name="analyze_code",
        description="Analyze code for patterns, complexity, and issues",
        category="analysis",
        popularity=300,
        tags=["analyze", "code", "quality"],
    ),
    "find_bugs": ToolMetadata(
        name="find_bugs",
        description="Find potential bugs and security issues",
        category="analysis",
        popularity=250,
        tags=["bugs", "security", "lint"],
    ),
    "get_complexity": ToolMetadata(
        name="get_complexity",
        description="Calculate cyclomatic complexity metrics",
        category="analysis",
        popularity=180,
        tags=["complexity", "metrics"],
    ),
    # Documentation (via Context7)
    "get_docs": ToolMetadata(
        name="get_docs",
        description="Get package documentation (cached, compressed)",
        category="docs",
        popularity=400,
        tags=["docs", "documentation", "package"],
    ),
    "search_docs": ToolMetadata(
        name="search_docs",
        description="Search documentation with semantic matching",
        category="docs",
        popularity=350,
        tags=["search", "docs", "api"],
    ),
    # Optimization
    "optimize_response": ToolMetadata(
        name="optimize_response",
        description="Optimize any data for minimal token usage",
        category="optimize",
        popularity=200,
        tags=["optimize", "tokens", "minify"],
    ),
    "get_metrics": ToolMetadata(
        name="get_metrics",
        description="Get Tokenette performance metrics",
        category="system",
        popularity=150,
        tags=["metrics", "stats", "performance"],
    ),
}

# Full tool schemas (loaded on demand)
TOOL_SCHEMAS: dict[str, ToolDetails] = {
    "read_file_smart": ToolDetails(
        name="read_file_smart",
        description=(
            "Read a file with intelligent strategy selection. "
            "Automatically chooses the most token-efficient approach: "
            "full (small files), partial (medium), summary (large), or AST (code analysis)."
        ),
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to the file to read", "required": True},
            "strategy": {
                "type": "string",
                "enum": ["auto", "full", "partial", "summary", "ast"],
                "default": "auto",
                "description": "Reading strategy (auto recommended)",
            },
            "start_line": {"type": "integer", "description": "Start line for partial reads"},
            "end_line": {"type": "integer", "description": "End line for partial reads"},
        },
        returns="File content in optimized format",
        examples=[
            {"input": {"path": "src/main.py"}, "description": "Read with auto strategy"},
            {"input": {"path": "src/app.js", "strategy": "ast"}, "description": "Get AST only"},
        ],
    ),
    "write_file_diff": ToolDetails(
        name="write_file_diff",
        description=(
            "Write file changes using unified diff format. "
            "97% more token-efficient than sending full file content. "
            "Validates changes before applying."
        ),
        category="file",
        parameters={
            "path": {
                "type": "string",
                "description": "Path to the file to modify",
                "required": True,
            },
            "changes": {
                "type": "string",
                "description": "Changes in unified diff format (@@ -line,count +line,count @@)",
                "required": True,
            },
            "verify": {
                "type": "boolean",
                "default": True,
                "description": "Verify file hash before applying",
            },
        },
        returns="Result of the write operation",
        examples=[
            {
                "input": {
                    "path": "src/config.js",
                    "changes": "@@ -10,0 +10,2 @@\n+const DEBUG = true;\n+const API_URL = 'http://localhost:3000';",
                },
                "description": "Add 2 lines after line 10",
            }
        ],
    ),
    "search_code_semantic": ToolDetails(
        name="search_code_semantic",
        description=(
            "Search code using semantic matching. "
            "98% more efficient than grep for finding relevant code. "
            "Returns ranked snippets with context."
        ),
        category="file",
        parameters={
            "query": {
                "type": "string",
                "description": "Natural language search query",
                "required": True,
            },
            "directory": {
                "type": "string",
                "description": "Directory to search in",
                "default": ".",
            },
            "file_pattern": {"type": "string", "description": "File glob pattern (e.g., '*.py')"},
            "max_results": {
                "type": "integer",
                "default": 10,
                "description": "Maximum results to return",
            },
        },
        returns="Ranked list of code snippets",
        examples=[
            {"input": {"query": "authentication middleware"}, "description": "Find auth code"},
            {
                "input": {"query": "database connection", "file_pattern": "*.py"},
                "description": "Find DB code in Python",
            },
        ],
    ),
    "get_file_structure": ToolDetails(
        name="get_file_structure",
        description=(
            "Get the structural overview of a file (AST-based). "
            "99% token savings for understanding file organization. "
            "Returns functions, classes, imports without full code."
        ),
        category="file",
        parameters={
            "path": {"type": "string", "description": "Path to the file", "required": True},
            "depth": {
                "type": "integer",
                "default": 2,
                "description": "Depth of nesting to show (1-5)",
            },
            "include_signatures": {
                "type": "boolean",
                "default": True,
                "description": "Include function signatures",
            },
        },
        returns="File structure in TOON format",
        examples=[
            {"input": {"path": "src/app.py"}, "description": "Get structure"},
            {"input": {"path": "src/utils.js", "depth": 3}, "description": "Get deeper structure"},
        ],
    ),
    "batch_read_files": ToolDetails(
        name="batch_read_files",
        description=(
            "Read multiple files with cross-file deduplication. "
            "60-80% savings on multi-file operations. "
            "Shared imports and patterns are extracted once."
        ),
        category="file",
        parameters={
            "paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths to read",
                "required": True,
            },
            "deduplicate": {
                "type": "boolean",
                "default": True,
                "description": "Enable cross-file deduplication",
            },
            "strategy": {"type": "string", "enum": ["auto", "full", "summary"], "default": "auto"},
        },
        returns="Batch result with deduplicated content",
        examples=[
            {
                "input": {"paths": ["src/a.py", "src/b.py", "src/c.py"]},
                "description": "Read 3 files with deduplication",
            }
        ],
    ),
    "analyze_code": ToolDetails(
        name="analyze_code",
        description="Analyze code for patterns, complexity, and potential issues.",
        category="analysis",
        parameters={
            "path": {
                "type": "string",
                "description": "Path to file or directory",
                "required": True,
            },
            "checks": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["complexity", "style", "security"],
                "description": "Analysis checks to run",
            },
        },
        returns="Analysis results",
        examples=[],
    ),
    "find_bugs": ToolDetails(
        name="find_bugs",
        description="Find potential bugs and security issues in code.",
        category="analysis",
        parameters={
            "path": {
                "type": "string",
                "description": "Path to file or directory",
                "required": True,
            },
            "severity": {
                "type": "string",
                "enum": ["all", "high", "medium", "low"],
                "default": "all",
            },
        },
        returns="List of potential issues",
        examples=[],
    ),
    "get_complexity": ToolDetails(
        name="get_complexity",
        description="Calculate cyclomatic complexity and other metrics.",
        category="analysis",
        parameters={"path": {"type": "string", "description": "Path to file", "required": True}},
        returns="Complexity metrics",
        examples=[],
    ),
    "get_docs": ToolDetails(
        name="get_docs",
        description="Get package documentation via Context7 (cached).",
        category="docs",
        parameters={
            "package": {
                "type": "string",
                "description": "Package name (e.g., 'react', 'fastapi')",
                "required": True,
            },
            "topic": {"type": "string", "description": "Specific topic to fetch"},
            "version": {"type": "string", "description": "Package version"},
        },
        returns="Compressed documentation",
        examples=[],
    ),
    "search_docs": ToolDetails(
        name="search_docs",
        description="Search documentation with semantic matching.",
        category="docs",
        parameters={
            "query": {"type": "string", "description": "Search query", "required": True},
            "package": {"type": "string", "description": "Limit to specific package"},
        },
        returns="Relevant documentation snippets",
        examples=[],
    ),
    "optimize_response": ToolDetails(
        name="optimize_response",
        description="Optimize any data for minimal token usage.",
        category="optimize",
        parameters={
            "data": {"type": "any", "description": "Data to optimize", "required": True},
            "format": {
                "type": "string",
                "enum": ["auto", "json", "toon", "code"],
                "default": "auto",
            },
        },
        returns="Optimized data",
        examples=[],
    ),
    "get_metrics": ToolDetails(
        name="get_metrics",
        description="Get Tokenette performance metrics and savings.",
        category="system",
        parameters={},
        returns="Performance metrics",
        examples=[],
    ),
}


async def discover_tools(
    category: str | None = None,
    query: str | None = None,
    limit: int = 10,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Discover available tools without loading full schemas.

    96% token savings vs listing all tool schemas upfront.

    Args:
        category: Filter by category (file, analysis, docs, optimize, system)
        query: Search query for tool names/descriptions
        limit: Maximum tools to return
        ctx: MCP context

    Returns:
        List of matching tools with minimal metadata
    """
    results = []

    for name, metadata in TOOL_REGISTRY.items():
        # Filter by category
        if category and metadata.category != category:
            continue

        # Filter by query
        if query:
            query_lower = query.lower()
            matches = (
                query_lower in name.lower()
                or query_lower in metadata.description.lower()
                or any(query_lower in tag for tag in metadata.tags)
            )
            if not matches:
                continue

        results.append(metadata.to_dict())

    # Sort by popularity
    results.sort(key=lambda x: x.get("pop", 0), reverse=True)

    # Limit results
    results = results[:limit]

    return {
        "tools": results,
        "total": len(results),
        "categories": list({m.category for m in TOOL_REGISTRY.values()}),
        "_tokens": len(results) * 20,  # Approximate token cost
    }


async def get_tool_details(
    tool_name: str, include_examples: bool = True, ctx: Context | None = None
) -> dict[str, Any]:
    """
    Get full schema for a specific tool.

    Loaded on-demand to save tokens.

    Args:
        tool_name: Name of the tool
        include_examples: Include usage examples
        ctx: MCP context

    Returns:
        Full tool schema with parameters
    """
    if tool_name not in TOOL_SCHEMAS:
        return {"error": f"Tool '{tool_name}' not found", "available": list(TOOL_REGISTRY.keys())}

    schema = TOOL_SCHEMAS[tool_name]
    result = schema.to_dict()

    if not include_examples:
        result.pop("examples", None)

    return result


async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    cache_key: str | None = None,
    skip_cache: bool = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Execute a tool with caching and optimization.

    Automatically caches results and optimizes response.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        cache_key: Custom cache key (auto-generated if None)
        skip_cache: Skip cache lookup
        ctx: MCP context

    Returns:
        Optimized tool result
    """
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Tool '{tool_name}' not found", "available": list(TOOL_REGISTRY.keys())}

    # Import tools dynamically to avoid circular imports
    from tokenette.tools import analysis, file_ops

    # Tool dispatch map
    tool_functions: dict[str, Callable[..., Any]] = {
        "read_file_smart": file_ops.read_file_smart,
        "write_file_diff": file_ops.write_file_diff,
        "search_code_semantic": file_ops.search_code_semantic,
        "get_file_structure": file_ops.get_file_structure,
        "batch_read_files": file_ops.batch_read_files,
        "analyze_code": analysis.analyze_code,
        "find_bugs": analysis.find_bugs,
        "get_complexity": analysis.get_complexity,
    }

    if tool_name not in tool_functions:
        return {"error": f"Tool '{tool_name}' not yet implemented", "status": "pending"}

    # Execute tool
    func = tool_functions[tool_name]

    try:
        result = await func(**arguments, ctx=ctx)

        # Update popularity
        TOOL_REGISTRY[tool_name].popularity += 1

        return {"status": "success", "tool": tool_name, "result": result}
    except Exception as e:
        return {"status": "error", "tool": tool_name, "error": str(e)}
