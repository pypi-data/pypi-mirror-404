"""
Workspace Intelligence Tools

Advanced workspace analysis, summarization, and insights.
- Project structure analysis
- Dependency mapping
- Code health metrics
- Smart context extraction
"""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ProjectInfo:
    """Information about a project."""

    name: str
    type: str  # python, node, rust, go, etc.
    root_path: str
    language: str
    framework: str | None
    package_manager: str | None
    entry_points: list[str]
    config_files: list[str]
    dependencies: dict[str, str]
    dev_dependencies: dict[str, str]
    scripts: dict[str, str]


@dataclass
class WorkspaceSummary:
    """Summarized workspace information."""

    total_files: int
    total_lines: int
    languages: dict[str, int]  # language -> file count
    structure: dict[str, Any]
    key_files: list[str]
    entry_points: list[str]
    token_estimate: int
    summary_text: str


@dataclass
class DependencyMap:
    """Dependency analysis result."""

    direct: list[dict[str, str]]
    dev: list[dict[str, str]]
    total_count: int
    outdated: list[dict[str, str]]
    security_issues: list[dict[str, str]]
    dependency_tree: dict[str, list[str]]


@dataclass
class CodeHealthMetrics:
    """Code health and quality metrics."""

    files_analyzed: int
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    comment_ratio: float
    avg_file_size: int
    largest_files: list[dict[str, Any]]
    complexity_hotspots: list[dict[str, Any]]
    duplication_estimate: float
    recommendations: list[str]


# File patterns for different project types
PROJECT_PATTERNS = {
    "python": {
        "markers": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile"],
        "package_managers": {
            "pyproject.toml": "uv/pip",
            "Pipfile": "pipenv",
            "requirements.txt": "pip",
        },
        "entry_points": ["main.py", "app.py", "__main__.py", "cli.py"],
        "extensions": [".py", ".pyi"],
    },
    "node": {
        "markers": ["package.json"],
        "package_managers": {"package.json": "npm", "yarn.lock": "yarn", "pnpm-lock.yaml": "pnpm"},
        "entry_points": ["index.js", "index.ts", "main.js", "app.js", "server.js"],
        "extensions": [".js", ".ts", ".jsx", ".tsx"],
    },
    "rust": {
        "markers": ["Cargo.toml"],
        "package_managers": {"Cargo.toml": "cargo"},
        "entry_points": ["src/main.rs", "src/lib.rs"],
        "extensions": [".rs"],
    },
    "go": {
        "markers": ["go.mod"],
        "package_managers": {"go.mod": "go mod"},
        "entry_points": ["main.go", "cmd/main.go"],
        "extensions": [".go"],
    },
}

# Ignored directories
IGNORED_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    ".cache",
    ".pytest_cache",
    ".mypy_cache",
    "coverage",
    ".tox",
}

# Ignored files
IGNORED_FILES = {
    ".DS_Store",
    "Thumbs.db",
    ".gitignore",
    ".env",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Cargo.lock",
    "go.sum",
}


async def detect_project_type(root_path: str) -> ProjectInfo:
    """
    Detect project type and gather information.

    Args:
        root_path: Path to project root

    Returns:
        ProjectInfo with detected information
    """
    root = Path(root_path)

    if not root.exists():
        return ProjectInfo(
            name="unknown",
            type="unknown",
            root_path=root_path,
            language="unknown",
            framework=None,
            package_manager=None,
            entry_points=[],
            config_files=[],
            dependencies={},
            dev_dependencies={},
            scripts={},
        )

    # Detect project type
    project_type = "unknown"
    language = "unknown"
    package_manager = None
    config_files = []

    for ptype, patterns in PROJECT_PATTERNS.items():
        for marker in patterns["markers"]:
            if (root / marker).exists():
                project_type = ptype
                language = ptype
                config_files.append(marker)

                # Detect package manager
                for pm_file, pm_name in patterns["package_managers"].items():
                    if (root / pm_file).exists():
                        package_manager = pm_name
                        break
                break
        if project_type != "unknown":
            break

    # Get project name
    name = root.name

    # Detect framework and dependencies
    framework = None
    dependencies = {}
    dev_dependencies = {}
    scripts = {}

    if project_type == "python" and (root / "pyproject.toml").exists():
        deps_info = _parse_pyproject(root / "pyproject.toml")
        dependencies = deps_info.get("dependencies", {})
        dev_dependencies = deps_info.get("dev_dependencies", {})
        name = deps_info.get("name", name)
        framework = _detect_python_framework(dependencies)

    elif project_type == "node" and (root / "package.json").exists():
        deps_info = _parse_package_json(root / "package.json")
        dependencies = deps_info.get("dependencies", {})
        dev_dependencies = deps_info.get("dev_dependencies", {})
        scripts = deps_info.get("scripts", {})
        name = deps_info.get("name", name)
        framework = _detect_node_framework(dependencies)

    # Find entry points
    entry_points = []
    if project_type in PROJECT_PATTERNS:
        for ep in PROJECT_PATTERNS[project_type]["entry_points"]:
            if (root / ep).exists():
                entry_points.append(ep)

    return ProjectInfo(
        name=name,
        type=project_type,
        root_path=root_path,
        language=language,
        framework=framework,
        package_manager=package_manager,
        entry_points=entry_points,
        config_files=config_files,
        dependencies=dependencies,
        dev_dependencies=dev_dependencies,
        scripts=scripts,
    )


def _parse_pyproject(path: Path) -> dict:
    """Parse pyproject.toml for project info."""
    try:
        import tomllib

        with open(path, "rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})
        dependencies = {}

        # Parse dependencies
        for dep in project.get("dependencies", []):
            name = dep.split("[")[0].split(">=")[0].split("==")[0].split("<")[0].strip()
            dependencies[name] = dep

        return {
            "name": project.get("name", ""),
            "dependencies": dependencies,
            "dev_dependencies": {},
        }
    except Exception:
        return {}


def _parse_package_json(path: Path) -> dict:
    """Parse package.json for project info."""
    try:
        data = json.loads(path.read_text())
        return {
            "name": data.get("name", ""),
            "dependencies": data.get("dependencies", {}),
            "dev_dependencies": data.get("devDependencies", {}),
            "scripts": data.get("scripts", {}),
        }
    except Exception:
        return {}


def _detect_python_framework(deps: dict) -> str | None:
    """Detect Python framework from dependencies."""
    frameworks = {
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "fastmcp": "FastMCP",
        "starlette": "Starlette",
        "aiohttp": "aiohttp",
        "tornado": "Tornado",
    }

    for dep, name in frameworks.items():
        if dep in deps:
            return name
    return None


def _detect_node_framework(deps: dict) -> str | None:
    """Detect Node.js framework from dependencies."""
    frameworks = {
        "next": "Next.js",
        "react": "React",
        "vue": "Vue",
        "express": "Express",
        "fastify": "Fastify",
        "nuxt": "Nuxt",
        "svelte": "Svelte",
        "angular": "Angular",
    }

    for dep, name in frameworks.items():
        if dep in deps:
            return name
    return None


async def get_workspace_summary(
    root_path: str, max_depth: int = 4, include_content_preview: bool = False
) -> WorkspaceSummary:
    """
    Generate a comprehensive workspace summary.

    Token-optimized summary of the entire workspace.

    Args:
        root_path: Path to workspace root
        max_depth: Maximum directory depth to traverse
        include_content_preview: Include file content previews

    Returns:
        WorkspaceSummary with key information
    """
    root = Path(root_path)

    total_files = 0
    total_lines = 0
    languages: dict[str, int] = {}
    key_files: list[str] = []
    structure: dict[str, Any] = {}

    # Key file patterns
    key_patterns = [
        "README.md",
        "readme.md",
        "README",
        "main.py",
        "app.py",
        "index.js",
        "index.ts",
        "package.json",
        "pyproject.toml",
        "Cargo.toml",
        "Dockerfile",
        "docker-compose.yml",
        ".env.example",
        "config.py",
        "settings.py",
    ]

    # Walk directory
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter ignored directories
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]

        rel_path = Path(dirpath).relative_to(root)
        depth = len(rel_path.parts)

        if depth > max_depth:
            continue

        for filename in filenames:
            if filename in IGNORED_FILES:
                continue

            file_path = Path(dirpath) / filename
            rel_file_path = str(file_path.relative_to(root))

            total_files += 1

            # Count by extension
            ext = file_path.suffix.lower()
            lang = _ext_to_language(ext)
            languages[lang] = languages.get(lang, 0) + 1

            # Check for key files
            if filename in key_patterns or any(p in filename for p in ["README", "config", "main"]):
                key_files.append(rel_file_path)

            # Count lines
            try:
                lines = len(file_path.read_text(errors="replace").split("\n"))
                total_lines += lines
            except Exception:
                pass

    # Build structure tree (simplified)
    structure = _build_structure_tree(root, max_depth=2)

    # Find entry points
    project_info = await detect_project_type(root_path)
    entry_points = project_info.entry_points

    # Token estimate
    token_estimate = total_lines * 3  # Rough estimate: 3 tokens per line average

    # Generate summary text
    summary_parts = [
        f"Project: {project_info.name} ({project_info.type})",
        f"Framework: {project_info.framework or 'None detected'}",
        f"Files: {total_files} | Lines: {total_lines:,}",
        f"Languages: {', '.join(f'{k}({v})' for k, v in sorted(languages.items(), key=lambda x: -x[1])[:5])}",
        f"Entry points: {', '.join(entry_points) or 'None found'}",
    ]

    summary_text = " | ".join(summary_parts)

    return WorkspaceSummary(
        total_files=total_files,
        total_lines=total_lines,
        languages=languages,
        structure=structure,
        key_files=key_files[:20],  # Limit to top 20
        entry_points=entry_points,
        token_estimate=token_estimate,
        summary_text=summary_text,
    )


def _ext_to_language(ext: str) -> str:
    """Map file extension to language name."""
    mapping = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "JavaScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".c": "C",
        ".cpp": "C++",
        ".h": "C/C++ Header",
        ".cs": "C#",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".vue": "Vue",
        ".svelte": "Svelte",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".less": "LESS",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".md": "Markdown",
        ".sql": "SQL",
        ".sh": "Shell",
        ".bash": "Shell",
    }
    return mapping.get(ext.lower(), "Other")


def _build_structure_tree(root: Path, max_depth: int = 2) -> dict:
    """Build a simplified directory structure tree."""
    tree: dict[str, Any] = {}

    for item in sorted(root.iterdir()):
        if item.name in IGNORED_DIRS or item.name.startswith("."):
            continue

        if item.is_dir():
            if max_depth > 0:
                tree[item.name + "/"] = _build_structure_tree(item, max_depth - 1)
            else:
                tree[item.name + "/"] = "..."
        else:
            if item.name not in IGNORED_FILES:
                tree[item.name] = None

    return tree


async def analyze_dependencies(root_path: str) -> DependencyMap:
    """
    Analyze project dependencies.

    Args:
        root_path: Path to project root

    Returns:
        DependencyMap with dependency analysis
    """
    project = await detect_project_type(root_path)

    direct = [{"name": k, "version": v} for k, v in project.dependencies.items()]
    dev = [{"name": k, "version": v} for k, v in project.dev_dependencies.items()]

    # Build simple dependency tree (would need actual resolution for accurate tree)
    dependency_tree = {d["name"]: [] for d in direct}

    return DependencyMap(
        direct=direct,
        dev=dev,
        total_count=len(direct) + len(dev),
        outdated=[],  # Would need network call to check
        security_issues=[],  # Would need security database
        dependency_tree=dependency_tree,
    )


async def get_code_health(root_path: str) -> CodeHealthMetrics:
    """
    Analyze code health metrics.

    Args:
        root_path: Path to project root

    Returns:
        CodeHealthMetrics with quality indicators
    """
    root = Path(root_path)

    files_analyzed = 0
    total_lines = 0
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    file_sizes: list[tuple[str, int]] = []

    # Code file extensions
    code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb", ".php"}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]

        for filename in filenames:
            file_path = Path(dirpath) / filename

            if file_path.suffix.lower() not in code_extensions:
                continue

            try:
                content = file_path.read_text(errors="replace")
                lines = content.split("\n")

                files_analyzed += 1
                file_lines = len(lines)
                total_lines += file_lines
                file_sizes.append((str(file_path.relative_to(root)), file_lines))

                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        blank_lines += 1
                    elif (
                        stripped.startswith("#")
                        or stripped.startswith("//")
                        or stripped.startswith("/*")
                    ):
                        comment_lines += 1
                    else:
                        code_lines += 1

            except Exception:
                pass

    # Calculate metrics
    comment_ratio = comment_lines / max(code_lines, 1)
    avg_file_size = total_lines // max(files_analyzed, 1)

    # Find largest files
    file_sizes.sort(key=lambda x: -x[1])
    largest_files = [{"file": f, "lines": l} for f, l in file_sizes[:10]]

    # Generate recommendations
    recommendations = []

    if comment_ratio < 0.05:
        recommendations.append("📝 Low comment ratio. Consider adding more documentation.")
    elif comment_ratio > 0.4:
        recommendations.append("📚 High comment ratio. Some comments may be redundant.")

    if avg_file_size > 500:
        recommendations.append(
            "📦 Large average file size. Consider splitting into smaller modules."
        )

    if largest_files and largest_files[0]["lines"] > 1000:
        recommendations.append(
            f"⚠️ {largest_files[0]['file']} is very large ({largest_files[0]['lines']} lines). Consider refactoring."
        )

    if files_analyzed < 5:
        recommendations.append("📊 Small codebase. Metrics may not be representative.")

    return CodeHealthMetrics(
        files_analyzed=files_analyzed,
        total_lines=total_lines,
        code_lines=code_lines,
        comment_lines=comment_lines,
        blank_lines=blank_lines,
        comment_ratio=round(comment_ratio, 3),
        avg_file_size=avg_file_size,
        largest_files=largest_files,
        complexity_hotspots=[],  # Would need AST analysis
        duplication_estimate=0.0,  # Would need duplicate detection
        recommendations=recommendations,
    )


async def extract_smart_context(
    root_path: str, query: str, max_tokens: int = 4000
) -> dict[str, Any]:
    """
    Extract the most relevant context for a query.

    Intelligently selects files and sections most relevant
    to the user's query, optimized for token budget.

    Args:
        root_path: Path to project root
        query: User's query or task description
        max_tokens: Maximum tokens to include

    Returns:
        Optimized context for the query
    """
    # Get workspace summary first
    summary = await get_workspace_summary(root_path)
    project = await detect_project_type(root_path)

    context_parts = []
    tokens_used = 0

    # Always include project summary (low token cost, high value)
    context_parts.append(
        {
            "type": "summary",
            "content": summary.summary_text,
            "tokens": len(summary.summary_text) // 4,
        }
    )
    tokens_used += len(summary.summary_text) // 4

    # Extract keywords from query
    keywords = _extract_keywords(query.lower())

    # Score files by relevance
    root = Path(root_path)
    scored_files: list[tuple[str, float, int]] = []  # (path, score, size)

    for key_file in summary.key_files:
        file_path = root / key_file
        if file_path.exists():
            try:
                content = file_path.read_text(errors="replace")
                score = _score_relevance(key_file, content.lower(), keywords)
                size = len(content) // 4  # Estimated tokens
                scored_files.append((key_file, score, size))
            except Exception:
                pass

    # Sort by relevance
    scored_files.sort(key=lambda x: -x[1])

    # Include files up to token limit
    included_files = []
    for file_path, score, size in scored_files:
        if tokens_used + size > max_tokens:
            # Try to include partial content
            remaining = max_tokens - tokens_used
            if remaining > 200:  # Worth including partial
                try:
                    content = (root / file_path).read_text(errors="replace")
                    truncated = content[: remaining * 4]  # Approximate char limit
                    included_files.append(
                        {
                            "file": file_path,
                            "content": truncated + "\n... (truncated)",
                            "relevance": round(score, 2),
                            "truncated": True,
                        }
                    )
                    tokens_used += remaining
                except Exception:
                    pass
            break

        try:
            content = (root / file_path).read_text(errors="replace")
            included_files.append(
                {
                    "file": file_path,
                    "content": content,
                    "relevance": round(score, 2),
                    "truncated": False,
                }
            )
            tokens_used += size
        except Exception:
            pass

    return {
        "project": {"name": project.name, "type": project.type, "framework": project.framework},
        "summary": summary.summary_text,
        "files": included_files,
        "tokens_used": tokens_used,
        "token_budget": max_tokens,
    }


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from text."""
    # Remove common words
    stop_words = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "what",
        "which",
        "who",
        "whom",
        "how",
        "when",
        "where",
        "why",
        "and",
        "or",
        "but",
        "if",
        "then",
        "else",
        "for",
        "to",
        "from",
        "with",
        "by",
        "at",
        "in",
        "on",
    }

    words = re.findall(r"\b\w+\b", text)
    return [w for w in words if w not in stop_words and len(w) > 2]


def _score_relevance(file_path: str, content: str, keywords: list[str]) -> float:
    """Score file relevance based on keywords."""
    score = 0.0

    # File name matches
    file_lower = file_path.lower()
    for kw in keywords:
        if kw in file_lower:
            score += 5.0

    # Content matches
    for kw in keywords:
        count = content.count(kw)
        score += min(count * 0.5, 3.0)  # Cap per keyword

    # Boost for key files
    key_patterns = ["main", "app", "config", "readme", "index"]
    for pattern in key_patterns:
        if pattern in file_lower:
            score += 2.0

    return score
