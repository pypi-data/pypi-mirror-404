"""
Git Operations Tools

Smart git integration with token-optimized output.
- Optimized diffs (context-aware, minified)
- Smart blame (only relevant sections)
- Commit history (compressed summaries)
- Branch analysis
"""

import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass
class GitDiff:
    """Optimized git diff result."""

    files_changed: int
    insertions: int
    deletions: int
    diff: str
    summary: str
    tokens_saved: int


@dataclass
class GitBlame:
    """Optimized git blame result."""

    file: str
    lines: list[dict[str, Any]]
    authors: list[str]
    summary: str


@dataclass
class GitHistory:
    """Compressed commit history."""

    commits: list[dict[str, str]]
    total_commits: int
    date_range: str
    summary: str


async def run_git_command(cmd: list[str], cwd: str | None = None) -> tuple[str, int]:
    """Run a git command asynchronously."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd
        )
        stdout, stderr = await proc.communicate()
        return stdout.decode("utf-8", errors="replace"), proc.returncode or 0
    except Exception as e:
        return str(e), 1


async def get_git_diff(
    path: str = ".",
    staged: bool = False,
    context_lines: int = 3,
    ignore_whitespace: bool = True,
    files: list[str] | None = None,
) -> GitDiff:
    """
    Get optimized git diff with smart compression.

    Args:
        path: Repository path
        staged: Show staged changes only
        context_lines: Lines of context (default 3, less = smaller)
        ignore_whitespace: Ignore whitespace changes
        files: Specific files to diff (optional)

    Returns:
        GitDiff with compressed output
    """
    cmd = ["git", "diff"]

    if staged:
        cmd.append("--staged")

    cmd.extend([f"-U{context_lines}"])

    if ignore_whitespace:
        cmd.append("-w")

    # Add stat for summary
    cmd.append("--stat")

    if files:
        cmd.extend(["--"] + files)

    stat_output, code = await run_git_command(cmd, cwd=path)

    if code != 0:
        return GitDiff(
            files_changed=0,
            insertions=0,
            deletions=0,
            diff="",
            summary="No changes or not a git repository",
            tokens_saved=0,
        )

    # Get actual diff without stat
    cmd_diff = ["git", "diff"]
    if staged:
        cmd_diff.append("--staged")
    cmd_diff.extend([f"-U{context_lines}"])
    if ignore_whitespace:
        cmd_diff.append("-w")
    if files:
        cmd_diff.extend(["--"] + files)

    diff_output, _ = await run_git_command(cmd_diff, cwd=path)

    # Parse stats
    lines = stat_output.strip().split("\n")
    summary_line = lines[-1] if lines else ""

    # Extract numbers from summary
    files_changed = 0
    insertions = 0
    deletions = 0

    if "file" in summary_line:
        parts = summary_line.split(",")
        for part in parts:
            part = part.strip()
            if "file" in part:
                files_changed = int(part.split()[0])
            elif "insertion" in part:
                insertions = int(part.split()[0])
            elif "deletion" in part:
                deletions = int(part.split()[0])

    # Compress diff by removing redundant headers
    compressed_diff = _compress_diff(diff_output)
    tokens_saved = (len(diff_output) - len(compressed_diff)) // 4

    return GitDiff(
        files_changed=files_changed,
        insertions=insertions,
        deletions=deletions,
        diff=compressed_diff,
        summary=f"{files_changed} files: +{insertions} -{deletions}",
        tokens_saved=max(0, tokens_saved),
    )


def _compress_diff(diff: str) -> str:
    """Compress diff by removing redundant information."""
    if not diff:
        return ""

    lines = diff.split("\n")
    compressed = []
    skip_next_header = False

    for line in lines:
        # Skip redundant diff headers
        if line.startswith("diff --git"):
            # Keep just the file path
            parts = line.split(" b/")
            if len(parts) > 1:
                compressed.append(f"=== {parts[1]} ===")
            skip_next_header = True
            continue

        if skip_next_header:
            if line.startswith("index ") or line.startswith("---") or line.startswith("+++"):
                continue
            skip_next_header = False

        # Keep actual changes
        if line.startswith("@@") or line.startswith("+") or line.startswith("-") or line.strip():
            compressed.append(line)

    return "\n".join(compressed)


async def get_git_blame(
    file_path: str,
    start_line: int | None = None,
    end_line: int | None = None,
    show_email: bool = False,
) -> GitBlame:
    """
    Get optimized git blame for a file or section.

    Args:
        file_path: Path to file
        start_line: Starting line (1-indexed)
        end_line: Ending line (inclusive)
        show_email: Include author emails

    Returns:
        GitBlame with compressed output
    """
    cmd = ["git", "blame", "--line-porcelain"]

    if start_line and end_line:
        cmd.extend([f"-L{start_line},{end_line}"])

    if show_email:
        cmd.append("-e")

    cmd.append(file_path)

    output, code = await run_git_command(cmd)

    if code != 0:
        return GitBlame(file=file_path, lines=[], authors=[], summary="Unable to get blame info")

    # Parse porcelain format
    lines = []
    authors = set()
    current_entry: dict[str, Any] = {}

    for line in output.split("\n"):
        if line.startswith("author "):
            current_entry["author"] = line[7:]
            authors.add(line[7:])
        elif line.startswith("author-time "):
            current_entry["time"] = line[12:]
        elif line.startswith("summary "):
            current_entry["commit_msg"] = line[8:]
        elif line.startswith("\t"):
            current_entry["code"] = line[1:]
            lines.append(current_entry.copy())
            current_entry = {}

    # Compress: group consecutive lines by same author
    compressed_lines = _compress_blame(lines)

    return GitBlame(
        file=file_path,
        lines=compressed_lines,
        authors=list(authors),
        summary=f"{len(lines)} lines, {len(authors)} authors",
    )


def _compress_blame(lines: list[dict]) -> list[dict]:
    """Compress blame by grouping consecutive lines by author."""
    if not lines:
        return []

    compressed = []
    current_group = {
        "author": lines[0].get("author", "unknown"),
        "start_line": 1,
        "end_line": 1,
        "commit_msg": lines[0].get("commit_msg", ""),
    }

    for i, line in enumerate(lines[1:], start=2):
        if line.get("author") == current_group["author"]:
            current_group["end_line"] = i
        else:
            compressed.append(current_group)
            current_group = {
                "author": line.get("author", "unknown"),
                "start_line": i,
                "end_line": i,
                "commit_msg": line.get("commit_msg", ""),
            }

    compressed.append(current_group)
    return compressed


async def get_git_history(
    path: str = ".",
    max_commits: int = 20,
    file_path: str | None = None,
    author: str | None = None,
    since: str | None = None,
    format_type: str = "compact",
) -> GitHistory:
    """
    Get compressed commit history.

    Args:
        path: Repository path
        max_commits: Maximum commits to return
        file_path: Filter by file
        author: Filter by author
        since: Date filter (e.g., "2 weeks ago")
        format_type: "compact" or "detailed"

    Returns:
        GitHistory with optimized output
    """
    fmt = "%h|%an|%ar|%s" if format_type == "compact" else "%H|%an|%ae|%ai|%s"

    cmd = ["git", "log", f"--format={fmt}", f"-n{max_commits}"]

    if author:
        cmd.append(f"--author={author}")
    if since:
        cmd.append(f"--since={since}")
    if file_path:
        cmd.extend(["--", file_path])

    output, code = await run_git_command(cmd, cwd=path)

    if code != 0:
        return GitHistory(
            commits=[], total_commits=0, date_range="", summary="Unable to get history"
        )

    commits = []
    for line in output.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|")
        if len(parts) >= 4:
            commits.append(
                {
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2] if format_type == "compact" else parts[3],
                    "message": parts[3] if format_type == "compact" else parts[4],
                }
            )

    # Get total count
    count_cmd = ["git", "rev-list", "--count", "HEAD"]
    count_output, _ = await run_git_command(count_cmd, cwd=path)
    total = int(count_output.strip()) if count_output.strip().isdigit() else len(commits)

    date_range = ""
    if commits:
        date_range = f"{commits[-1]['date']} to {commits[0]['date']}"

    return GitHistory(
        commits=commits,
        total_commits=total,
        date_range=date_range,
        summary=f"Showing {len(commits)}/{total} commits",
    )


async def get_git_status(path: str = ".") -> dict[str, Any]:
    """
    Get optimized git status.

    Returns compact status with file counts by category.
    """
    cmd = ["git", "status", "--porcelain", "-b"]
    output, code = await run_git_command(cmd, cwd=path)

    if code != 0:
        return {"error": "Not a git repository", "files": []}

    lines = output.strip().split("\n")
    branch_line = lines[0] if lines else ""
    file_lines = lines[1:] if len(lines) > 1 else []

    # Parse branch info
    branch = branch_line.replace("## ", "").split("...")[0] if branch_line else "unknown"

    # Categorize files
    staged = []
    unstaged = []
    untracked = []

    for line in file_lines:
        if not line:
            continue
        status = line[:2]
        file_path = line[3:]

        if status[0] != " " and status[0] != "?":
            staged.append(file_path)
        if status[1] != " " and status[1] != "?":
            unstaged.append(file_path)
        if status == "??":
            untracked.append(file_path)

    return {
        "branch": branch,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "summary": f"Branch: {branch} | Staged: {len(staged)} | Modified: {len(unstaged)} | Untracked: {len(untracked)}",
    }


async def get_git_branches(
    path: str = ".", remote: bool = False, merged: bool | None = None
) -> dict[str, Any]:
    """
    Get branch information.

    Args:
        path: Repository path
        remote: Include remote branches
        merged: Filter by merged status (True/False/None for all)

    Returns:
        Branch list with current branch highlighted
    """
    cmd = ["git", "branch", "--format=%(refname:short)|%(upstream:short)|%(HEAD)"]

    if remote:
        cmd.append("-a")
    if merged is True:
        cmd.append("--merged")
    elif merged is False:
        cmd.append("--no-merged")

    output, code = await run_git_command(cmd, cwd=path)

    if code != 0:
        return {"error": "Unable to get branches", "branches": []}

    branches = []
    current = None

    for line in output.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|")
        name = parts[0]
        upstream = parts[1] if len(parts) > 1 else ""
        is_current = parts[2] == "*" if len(parts) > 2 else False

        branches.append({"name": name, "upstream": upstream, "current": is_current})

        if is_current:
            current = name

    return {"current": current, "branches": branches, "total": len(branches)}
