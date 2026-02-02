"""
Code Analysis Tools

Provides code analysis capabilities:
- analyze_code: Patterns, complexity, and issues
- find_bugs: Potential bugs and security issues
- get_complexity: Cyclomatic complexity metrics
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import aiofiles
from fastmcp import Context


@dataclass
class Issue:
    """A detected code issue."""

    type: str  # "bug", "security", "style", "performance"
    severity: str  # "high", "medium", "low"
    message: str
    file: str
    line: int
    code: str = ""
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "code": self.code[:50] if self.code else "",
            "suggestion": self.suggestion,
        }


@dataclass
class ComplexityMetrics:
    """Code complexity metrics."""

    file: str
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    functions: int = 0
    classes: int = 0
    max_nesting: int = 0
    maintainability_index: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "cyclomatic": self.cyclomatic_complexity,
            "loc": self.lines_of_code,
            "functions": self.functions,
            "classes": self.classes,
            "max_nesting": self.max_nesting,
            "maintainability": round(self.maintainability_index, 1),
        }


# Common bug patterns
BUG_PATTERNS = {
    "python": [
        {
            "pattern": r"except\s*:",
            "type": "bug",
            "severity": "medium",
            "message": "Bare except clause catches all exceptions including KeyboardInterrupt",
            "suggestion": "Use 'except Exception:' or specific exception types",
        },
        {
            "pattern": r"eval\s*\(",
            "type": "security",
            "severity": "high",
            "message": "Use of eval() is a security risk",
            "suggestion": "Use ast.literal_eval() for safe evaluation",
        },
        {
            "pattern": r"exec\s*\(",
            "type": "security",
            "severity": "high",
            "message": "Use of exec() is a security risk",
            "suggestion": "Avoid exec() or sanitize input carefully",
        },
        {
            "pattern": r"password\s*=\s*['\"]",
            "type": "security",
            "severity": "high",
            "message": "Hardcoded password detected",
            "suggestion": "Use environment variables or secrets manager",
        },
        {
            "pattern": r"api_key\s*=\s*['\"]",
            "type": "security",
            "severity": "high",
            "message": "Hardcoded API key detected",
            "suggestion": "Use environment variables",
        },
        {
            "pattern": r"==\s*True|==\s*False",
            "type": "style",
            "severity": "low",
            "message": "Comparison to True/False is unnecessary",
            "suggestion": "Use 'if condition:' or 'if not condition:'",
        },
        {
            "pattern": r"from\s+\w+\s+import\s+\*",
            "type": "style",
            "severity": "medium",
            "message": "Wildcard import pollutes namespace",
            "suggestion": "Import specific names",
        },
        {
            "pattern": r"time\.sleep\s*\(\s*\d{2,}",
            "type": "performance",
            "severity": "medium",
            "message": "Long sleep detected",
            "suggestion": "Consider async or event-based approach",
        },
    ],
    "javascript": [
        {
            "pattern": r"eval\s*\(",
            "type": "security",
            "severity": "high",
            "message": "Use of eval() is a security risk",
            "suggestion": "Avoid eval() entirely",
        },
        {
            "pattern": r"innerHTML\s*=",
            "type": "security",
            "severity": "high",
            "message": "innerHTML assignment can lead to XSS",
            "suggestion": "Use textContent or sanitize HTML",
        },
        {
            "pattern": r"==\s+|!=\s+",
            "type": "bug",
            "severity": "medium",
            "message": "Loose equality can cause unexpected behavior",
            "suggestion": "Use === and !== for strict equality",
        },
        {
            "pattern": r"var\s+\w+",
            "type": "style",
            "severity": "low",
            "message": "Using var instead of let/const",
            "suggestion": "Use let or const for block-scoped variables",
        },
        {
            "pattern": r"password\s*[=:]\s*['\"]",
            "type": "security",
            "severity": "high",
            "message": "Hardcoded password detected",
            "suggestion": "Use environment variables",
        },
        {
            "pattern": r"console\.log",
            "type": "style",
            "severity": "low",
            "message": "console.log left in code",
            "suggestion": "Remove or use proper logging",
        },
    ],
}


def _detect_language(path: Path) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
    }
    return ext_map.get(path.suffix.lower(), "unknown")


async def analyze_code(
    path: str, checks: list[str] | None = None, ctx: Context | None = None
) -> dict[str, Any]:
    """
    Analyze code for patterns, complexity, and potential issues.

    Args:
        path: Path to file or directory
        checks: Analysis checks to run (complexity, style, security)
        ctx: MCP context

    Returns:
        Analysis results
    """
    if checks is None:
        checks = ["complexity", "style", "security"]

    file_path = Path(path)

    if not file_path.exists():
        return {"error": f"Path not found: {path}"}

    results = {"path": path, "checks": checks, "issues": [], "metrics": {}, "summary": {}}

    if file_path.is_file():
        files = [file_path]
    else:
        # Get all code files in directory
        files = (
            list(file_path.rglob("*.py"))
            + list(file_path.rglob("*.js"))
            + list(file_path.rglob("*.ts"))
        )

    all_issues = []
    all_metrics = []

    for f in files[:20]:  # Limit to 20 files
        _detect_language(f)

        async with aiofiles.open(f, encoding="utf-8", errors="replace") as file:
            await file.read()

        # Run complexity analysis
        if "complexity" in checks:
            metrics = await get_complexity(str(f), ctx=ctx)
            if "metrics" in metrics:
                all_metrics.append(metrics["metrics"])

        # Run bug/security/style checks
        if "security" in checks or "style" in checks:
            issues = await find_bugs(
                str(f), severity="all" if "style" in checks else "high", ctx=ctx
            )
            if "issues" in issues:
                all_issues.extend(issues["issues"])

    # Summarize results
    results["issues"] = all_issues
    results["metrics"] = all_metrics
    results["summary"] = {
        "files_analyzed": len(files),
        "total_issues": len(all_issues),
        "high_severity": sum(1 for i in all_issues if i.get("severity") == "high"),
        "medium_severity": sum(1 for i in all_issues if i.get("severity") == "medium"),
        "low_severity": sum(1 for i in all_issues if i.get("severity") == "low"),
        "avg_complexity": (
            sum(m.get("cyclomatic", 0) for m in all_metrics) / len(all_metrics)
            if all_metrics
            else 0
        ),
    }

    return results


async def find_bugs(
    path: str, severity: Literal["all", "high", "medium", "low"] = "all", ctx: Context | None = None
) -> dict[str, Any]:
    """
    Find potential bugs and security issues in code.

    Args:
        path: Path to file
        severity: Filter by severity level
        ctx: MCP context

    Returns:
        List of potential issues
    """
    file_path = Path(path)

    if not file_path.exists():
        return {"error": f"File not found: {path}"}

    language = _detect_language(file_path)
    patterns = BUG_PATTERNS.get(language, BUG_PATTERNS.get("python", []))

    async with aiofiles.open(file_path, encoding="utf-8", errors="replace") as f:
        content = await f.read()

    lines = content.split("\n")
    issues = []

    for pattern_info in patterns:
        # Filter by severity
        if severity != "all" and pattern_info["severity"] != severity:
            continue

        pattern = pattern_info["pattern"]
        regex = re.compile(pattern, re.IGNORECASE)

        for i, line in enumerate(lines, 1):
            if regex.search(line):
                issue = Issue(
                    type=pattern_info["type"],
                    severity=pattern_info["severity"],
                    message=pattern_info["message"],
                    file=str(file_path),
                    line=i,
                    code=line.strip(),
                    suggestion=pattern_info.get("suggestion", ""),
                )
                issues.append(issue.to_dict())

    return {
        "path": path,
        "language": language,
        "issues": issues,
        "total": len(issues),
        "by_severity": {
            "high": sum(1 for i in issues if i["severity"] == "high"),
            "medium": sum(1 for i in issues if i["severity"] == "medium"),
            "low": sum(1 for i in issues if i["severity"] == "low"),
        },
    }


async def get_complexity(path: str, ctx: Context | None = None) -> dict[str, Any]:
    """
    Calculate cyclomatic complexity and other metrics.

    Cyclomatic complexity measures the number of linearly independent
    paths through a program's source code.

    Args:
        path: Path to file
        ctx: MCP context

    Returns:
        Complexity metrics
    """
    file_path = Path(path)

    if not file_path.exists():
        return {"error": f"File not found: {path}"}

    async with aiofiles.open(file_path, encoding="utf-8", errors="replace") as f:
        content = await f.read()

    language = _detect_language(file_path)
    lines = content.split("\n")

    metrics = ComplexityMetrics(file=str(file_path))
    metrics.lines_of_code = len([l for l in lines if l.strip() and not l.strip().startswith("#")])

    if language == "python":
        try:
            tree = ast.parse(content)
            metrics = _analyze_python_complexity(tree, metrics)
        except SyntaxError:
            # Fallback to regex-based analysis
            metrics = _analyze_complexity_regex(content, metrics)
    else:
        metrics = _analyze_complexity_regex(content, metrics)

    # Calculate maintainability index (simplified)
    # MI = 171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(LOC)
    import math

    volume = max(1, metrics.lines_of_code * 10)  # Simplified Halstead volume
    metrics.maintainability_index = max(
        0,
        min(
            100,
            171
            - 5.2 * math.log(volume)
            - 0.23 * metrics.cyclomatic_complexity
            - 16.2 * math.log(max(1, metrics.lines_of_code)),
        ),
    )

    return {
        "path": path,
        "language": language,
        "metrics": metrics.to_dict(),
        "rating": _complexity_rating(metrics.cyclomatic_complexity),
    }


def _analyze_python_complexity(tree: ast.AST, metrics: ComplexityMetrics) -> ComplexityMetrics:
    """Analyze Python AST for complexity metrics."""

    class ComplexityVisitor(ast.NodeVisitor):
        def __init__(self):
            self.complexity = 1
            self.max_depth = 0
            self.current_depth = 0
            self.functions = 0
            self.classes = 0

        def visit_If(self, node):
            self.complexity += 1
            self._update_depth(1)
            self.generic_visit(node)
            self._update_depth(-1)

        def visit_For(self, node):
            self.complexity += 1
            self._update_depth(1)
            self.generic_visit(node)
            self._update_depth(-1)

        def visit_While(self, node):
            self.complexity += 1
            self._update_depth(1)
            self.generic_visit(node)
            self._update_depth(-1)

        def visit_Try(self, node):
            self.complexity += len(node.handlers)
            self.generic_visit(node)

        def visit_BoolOp(self, node):
            self.complexity += len(node.values) - 1
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            self.functions += 1
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            self.functions += 1
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            self.classes += 1
            self.generic_visit(node)

        def _update_depth(self, delta):
            self.current_depth += delta
            self.max_depth = max(self.max_depth, self.current_depth)

    visitor = ComplexityVisitor()
    visitor.visit(tree)

    metrics.cyclomatic_complexity = visitor.complexity
    metrics.max_nesting = visitor.max_depth
    metrics.functions = visitor.functions
    metrics.classes = visitor.classes

    return metrics


def _analyze_complexity_regex(content: str, metrics: ComplexityMetrics) -> ComplexityMetrics:
    """Regex-based complexity analysis for any language."""
    # Count decision points
    decision_patterns = [
        r"\bif\b",
        r"\belse\b",
        r"\belif\b",
        r"\bfor\b",
        r"\bwhile\b",
        r"\band\b",
        r"\bor\b",
        r"\btry\b",
        r"\bcatch\b",
        r"\bexcept\b",
        r"\bcase\b",
        r"\?.*:",  # Ternary
    ]

    complexity = 1
    for pattern in decision_patterns:
        complexity += len(re.findall(pattern, content))

    # Count functions/classes
    metrics.functions = len(re.findall(r"\bdef\s+\w+|\bfunction\s+\w+|=>\s*{", content))
    metrics.classes = len(re.findall(r"\bclass\s+\w+", content))

    # Estimate nesting (count indentation levels)
    lines = content.split("\n")
    max_indent = 0
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent // 4)  # Assume 4-space indent

    metrics.cyclomatic_complexity = complexity
    metrics.max_nesting = max_indent

    return metrics


def _complexity_rating(complexity: int) -> str:
    """Rate complexity level."""
    if complexity <= 5:
        return "A (low complexity, easy to maintain)"
    elif complexity <= 10:
        return "B (moderate complexity)"
    elif complexity <= 20:
        return "C (high complexity, consider refactoring)"
    elif complexity <= 30:
        return "D (very high complexity, refactor recommended)"
    else:
        return "F (extreme complexity, refactor required)"
