"""
Tokenette Tools Package

Contains all MCP tools organized by category:
- Meta tools: discover_tools, get_tool_details, execute_tool
- File tools: read_file_smart, write_file_diff, search_code
- Analysis tools: analyze_code, get_file_structure, find_bugs
- Documentation tools: get_docs, search_docs
- Git tools: get_git_diff, get_git_blame, get_git_history, get_git_status
- Prompt tools: build_prompt, list_templates, PromptBuilder
- Token tools: count_tokens, estimate_cost, BudgetTracker
- Workspace tools: detect_project_type, get_workspace_summary, get_code_health
"""

from tokenette.tools.analysis import analyze_code, find_bugs, get_complexity
from tokenette.tools.context7 import (
    Context7Client,
    fetch_library_docs,
    get_context7_client,
    resolve_library,
    search_library_docs,
)
from tokenette.tools.file_ops import (
    batch_read_files,
    get_file_structure,
    read_file_smart,
    search_code_semantic,
    write_file_diff,
)
from tokenette.tools.git_ops import (
    GitBlame,
    GitDiff,
    GitHistory,
    get_git_blame,
    get_git_branches,
    get_git_diff,
    get_git_history,
    get_git_status,
)
from tokenette.tools.meta import discover_tools, execute_tool, get_tool_details
from tokenette.tools.prompts import (
    BuiltPrompt,
    PromptBuilder,
    PromptCategory,
    PromptTemplate,
    build_prompt,
    get_prompt_builder,
    list_templates,
)
from tokenette.tools.tokens import (
    BudgetStatus,
    BudgetTracker,
    CostEstimate,
    TokenCount,
    compare_model_costs,
    count_tokens,
    count_tokens_in_file,
    estimate_cost,
    get_budget_tracker,
)
from tokenette.tools.workspace import (
    CodeHealthMetrics,
    DependencyMap,
    ProjectInfo,
    WorkspaceSummary,
    analyze_dependencies,
    detect_project_type,
    extract_smart_context,
    get_code_health,
    get_workspace_summary,
)

__all__ = [
    # Meta tools
    "discover_tools",
    "get_tool_details",
    "execute_tool",
    # File tools
    "read_file_smart",
    "write_file_diff",
    "search_code_semantic",
    "get_file_structure",
    "batch_read_files",
    # Analysis tools
    "analyze_code",
    "find_bugs",
    "get_complexity",
    # Context7 / Documentation tools
    "resolve_library",
    "fetch_library_docs",
    "search_library_docs",
    "get_context7_client",
    "Context7Client",
    # Git tools
    "get_git_diff",
    "get_git_blame",
    "get_git_history",
    "get_git_status",
    "get_git_branches",
    "GitDiff",
    "GitBlame",
    "GitHistory",
    # Prompt tools
    "build_prompt",
    "list_templates",
    "get_prompt_builder",
    "PromptBuilder",
    "PromptTemplate",
    "BuiltPrompt",
    "PromptCategory",
    # Token tools
    "count_tokens",
    "count_tokens_in_file",
    "estimate_cost",
    "compare_model_costs",
    "get_budget_tracker",
    "BudgetTracker",
    "TokenCount",
    "CostEstimate",
    "BudgetStatus",
    # Workspace tools
    "detect_project_type",
    "get_workspace_summary",
    "analyze_dependencies",
    "get_code_health",
    "extract_smart_context",
    "ProjectInfo",
    "WorkspaceSummary",
    "DependencyMap",
    "CodeHealthMetrics",
]
