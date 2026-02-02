"""
Token & Budget Management Tools

Tools for counting tokens, estimating costs, and managing budgets.
Essential for optimizing AI interactions and staying within limits.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class TokenCount:
    """Result of token counting."""

    text_length: int
    estimated_tokens: int
    breakdown: dict[str, int] = field(default_factory=dict)


@dataclass
class CostEstimate:
    """Cost estimate for a model interaction."""

    model: str
    input_tokens: int
    output_tokens_estimate: int
    multiplier: float
    premium_requests_cost: float
    dollar_cost: float | None  # For token-based pricing
    breakdown: dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetStatus:
    """Current budget status."""

    monthly_limit: int
    used: float
    remaining: float
    percentage_used: float
    days_remaining: int
    daily_budget: float
    on_track: bool
    recommendations: list[str]


# Token estimation patterns
CODE_PATTERNS = {
    "python": {
        "avg_tokens_per_char": 0.28,  # Python is more readable
        "keyword_weight": 1.2,
    },
    "javascript": {
        "avg_tokens_per_char": 0.30,
        "keyword_weight": 1.1,
    },
    "typescript": {
        "avg_tokens_per_char": 0.32,  # Type annotations add tokens
        "keyword_weight": 1.15,
    },
    "default": {
        "avg_tokens_per_char": 0.25,  # ~4 chars per token
        "keyword_weight": 1.0,
    },
}

# Model pricing (tokens-based for some, multiplier for GitHub Copilot)
MODEL_COSTS = {
    # GitHub Copilot Pro (multiplier-based, 300 premium/month)
    "gpt-4.1": {"multiplier": 0, "tier": "free"},
    "gpt-4o": {"multiplier": 0, "tier": "free"},
    "gpt-4.1-mini": {"multiplier": 0, "tier": "free"},
    "gemini-2.0-flash": {"multiplier": 0.25, "tier": "cheap"},
    "o4-mini": {"multiplier": 0.33, "tier": "cheap"},
    "o3-mini": {"multiplier": 0.33, "tier": "cheap"},
    "claude-sonnet-4": {"multiplier": 1.0, "tier": "moderate"},
    "gemini-2.5-pro": {"multiplier": 1.0, "tier": "moderate"},
    "claude-opus-4.5": {"multiplier": 3.0, "tier": "expensive"},
    "claude-opus-4": {"multiplier": 10.0, "tier": "expensive"},
    "gpt-4.5": {"multiplier": 50.0, "tier": "avoid"},
    # Claude Code (token-based, per 1M tokens)
    "claude-sonnet-4.5-api": {"input_per_1m": 3.00, "output_per_1m": 15.00, "tier": "api"},
    "claude-opus-4.5-api": {"input_per_1m": 15.00, "output_per_1m": 75.00, "tier": "api"},
}


def count_tokens(text: str, language: str | None = None, detailed: bool = False) -> TokenCount:
    """
    Estimate token count for text/code.

    Uses language-aware heuristics for better accuracy.
    For exact counts, would need a real tokenizer.

    Args:
        text: Text or code to count
        language: Programming language for better estimation
        detailed: Include detailed breakdown

    Returns:
        TokenCount with estimates
    """
    text_length = len(text)

    # Get language-specific patterns
    lang_key = (language or "default").lower()
    patterns = CODE_PATTERNS.get(lang_key, CODE_PATTERNS["default"])

    # Base estimation
    base_tokens = int(text_length * patterns["avg_tokens_per_char"])

    breakdown = {}
    if detailed:
        # Count specific elements
        breakdown["lines"] = text.count("\n") + 1
        breakdown["words"] = len(text.split())
        breakdown["chars"] = text_length

        # Code-specific counts
        if language:
            breakdown["strings"] = len(re.findall(r'["\'].*?["\']', text))
            breakdown["comments"] = len(re.findall(r"#.*|//.*|/\*.*?\*/", text, re.DOTALL))
            breakdown["numbers"] = len(re.findall(r"\b\d+\.?\d*\b", text))

    # Adjust for special content
    adjustments = 0

    # Whitespace is efficient (multiple spaces = 1 token usually)
    whitespace_ratio = len(re.findall(r"\s+", text)) / max(text_length, 1)
    if whitespace_ratio > 0.2:
        adjustments -= int(base_tokens * 0.1)

    # Long strings are token-expensive
    long_strings = re.findall(r'["\'][^"\']{50,}["\']', text)
    if long_strings:
        adjustments += len(long_strings) * 10

    # URLs and paths are expensive
    urls = re.findall(r"https?://\S+", text)
    adjustments += len(urls) * 5

    final_tokens = max(1, base_tokens + adjustments)

    if detailed:
        breakdown["base_estimate"] = base_tokens
        breakdown["adjustments"] = adjustments

    return TokenCount(text_length=text_length, estimated_tokens=final_tokens, breakdown=breakdown)


def count_tokens_in_file(file_path: str, detailed: bool = False) -> TokenCount:
    """Count tokens in a file."""
    path = Path(file_path)

    if not path.exists():
        return TokenCount(text_length=0, estimated_tokens=0, breakdown={"error": "File not found"})

    content = path.read_text(errors="replace")
    language = _detect_language(path.suffix)

    return count_tokens(content, language=language, detailed=detailed)


def _detect_language(suffix: str) -> str:
    """Detect language from file extension."""
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
    }
    return mapping.get(suffix.lower(), "default")


def estimate_cost(
    model: str,
    input_text: str | int,
    output_estimate: int = 500,
    context: str = "copilot",  # "copilot" or "api"
) -> CostEstimate:
    """
    Estimate the cost of a model interaction.

    Args:
        model: Model name
        input_text: Input text or token count
        output_estimate: Estimated output tokens
        context: "copilot" for GitHub Copilot, "api" for direct API

    Returns:
        CostEstimate with breakdown
    """
    # Get input tokens
    if isinstance(input_text, str):
        input_tokens = count_tokens(input_text).estimated_tokens
    else:
        input_tokens = input_text

    # Get model info
    model_info = MODEL_COSTS.get(model, MODEL_COSTS.get("gpt-4.1"))

    if context == "copilot":
        multiplier = model_info.get("multiplier", 1.0)
        return CostEstimate(
            model=model,
            input_tokens=input_tokens,
            output_tokens_estimate=output_estimate,
            multiplier=multiplier,
            premium_requests_cost=multiplier,
            dollar_cost=None,  # Copilot is subscription
            breakdown={
                "tier": model_info.get("tier", "unknown"),
                "uses_per_month_at_this_rate": int(300 / max(multiplier, 0.01))
                if multiplier > 0
                else "unlimited",
            },
        )
    else:
        # API pricing
        input_cost = (input_tokens / 1_000_000) * model_info.get("input_per_1m", 3.00)
        output_cost = (output_estimate / 1_000_000) * model_info.get("output_per_1m", 15.00)
        total_cost = input_cost + output_cost

        return CostEstimate(
            model=model,
            input_tokens=input_tokens,
            output_tokens_estimate=output_estimate,
            multiplier=0,
            premium_requests_cost=0,
            dollar_cost=round(total_cost, 6),
            breakdown={
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "total": round(total_cost, 6),
            },
        )


class BudgetTracker:
    """Track and manage token/request budgets."""

    def __init__(self, monthly_limit: int = 300, reset_day: int = 1):
        self.monthly_limit = monthly_limit
        self.reset_day = reset_day
        self.used: float = 0.0
        self.history: list[dict] = []
        self.start_date = datetime.now().replace(day=reset_day)

    def record_usage(
        self, model: str, multiplier: float, tokens_in: int = 0, tokens_out: int = 0
    ) -> None:
        """Record a usage event."""
        self.used += multiplier
        self.history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "model": model,
                "multiplier": multiplier,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "running_total": self.used,
            }
        )

    def get_status(self) -> BudgetStatus:
        """Get current budget status with recommendations."""
        remaining = self.monthly_limit - self.used
        percentage = (self.used / self.monthly_limit) * 100

        # Calculate days remaining in billing cycle
        now = datetime.now()
        if now.day >= self.reset_day:
            next_reset = now.replace(day=self.reset_day) + timedelta(days=32)
            next_reset = next_reset.replace(day=self.reset_day)
        else:
            next_reset = now.replace(day=self.reset_day)

        days_remaining = (next_reset - now).days
        daily_budget = remaining / max(days_remaining, 1)

        # Check if on track
        expected_usage = (self.monthly_limit / 30) * (30 - days_remaining)
        on_track = self.used <= expected_usage * 1.1  # 10% buffer

        # Generate recommendations
        recommendations = []

        if percentage > 80:
            recommendations.append(
                "⚠️ Budget critically low. Use free models (gpt-4.1) for remaining tasks."
            )
        elif percentage > 60:
            recommendations.append("📊 Over 60% used. Consider cheaper models for simple tasks.")

        if daily_budget < 5:
            recommendations.append(
                f"📅 Daily budget: {daily_budget:.1f} requests. Batch operations when possible."
            )

        if not on_track:
            recommendations.append("📈 Usage ahead of schedule. Reduce expensive model usage.")

        # Model-specific recommendations
        expensive_count = sum(1 for h in self.history if h["multiplier"] >= 3)
        if expensive_count > 10:
            recommendations.append(
                "💡 High expensive model usage. Consider o4-mini (0.33×) for debugging."
            )

        return BudgetStatus(
            monthly_limit=self.monthly_limit,
            used=self.used,
            remaining=remaining,
            percentage_used=round(percentage, 1),
            days_remaining=days_remaining,
            daily_budget=round(daily_budget, 2),
            on_track=on_track,
            recommendations=recommendations,
        )

    def reset(self) -> None:
        """Reset budget for new billing cycle."""
        self.used = 0.0
        self.history.clear()
        self.start_date = datetime.now()

    def get_usage_by_model(self) -> dict[str, float]:
        """Get usage breakdown by model."""
        usage: dict[str, float] = {}
        for entry in self.history:
            model = entry["model"]
            usage[model] = usage.get(model, 0) + entry["multiplier"]
        return usage

    def get_daily_usage(self, days: int = 7) -> list[dict]:
        """Get daily usage for the last N days."""
        daily: dict[str, float] = {}
        cutoff = datetime.now() - timedelta(days=days)

        for entry in self.history:
            ts = datetime.fromisoformat(entry["timestamp"])
            if ts >= cutoff:
                date_key = ts.strftime("%Y-%m-%d")
                daily[date_key] = daily.get(date_key, 0) + entry["multiplier"]

        return [{"date": k, "usage": v} for k, v in sorted(daily.items())]


# Singleton tracker
_budget_tracker: BudgetTracker | None = None


def get_budget_tracker(monthly_limit: int = 300) -> BudgetTracker:
    """Get the budget tracker singleton."""
    global _budget_tracker
    if _budget_tracker is None:
        _budget_tracker = BudgetTracker(monthly_limit)
    return _budget_tracker


def compare_model_costs(input_text: str, output_estimate: int = 500) -> list[dict]:
    """
    Compare costs across all available models.

    Useful for choosing the right model for a task.
    """
    _ = count_tokens(input_text).estimated_tokens  # For future cost calculation
    _ = output_estimate  # Reserved for future use

    comparisons = []

    for model, info in MODEL_COSTS.items():
        if "multiplier" in info:  # Copilot model
            multiplier = info["multiplier"]
            uses_per_month = int(300 / max(multiplier, 0.01)) if multiplier > 0 else 999999

            comparisons.append(
                {
                    "model": model,
                    "tier": info.get("tier", "unknown"),
                    "multiplier": multiplier,
                    "uses_per_month": uses_per_month if uses_per_month < 999999 else "unlimited",
                    "cost_type": "premium_request",
                }
            )

    # Sort by multiplier (cheapest first)
    comparisons.sort(
        key=lambda x: x["multiplier"] if isinstance(x["multiplier"], (int, float)) else 0
    )

    return comparisons
