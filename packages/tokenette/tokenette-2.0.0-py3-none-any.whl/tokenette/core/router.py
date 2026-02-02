"""
Intelligent Task Router

Routes tasks to the optimal model based on:
1. Task complexity detection (keyword + scope + domain signals)
2. Real model performance benchmarks
3. Cost budget awareness (tracks premium request usage)
4. Adaptive learning (improves from past interactions)
5. Auto-mode discount exploitation (10% savings)

"Make any model perform like GPT-4.5 quality at GPT-4o cost."
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from tokenette.config import RouterConfig


class Complexity(Enum):
    """Task complexity levels."""

    TRIVIAL = 1  # 1-liner, rename, add comment
    SIMPLE = 2  # Single function, basic CRUD
    MODERATE = 3  # Multi-function, small refactor
    COMPLEX = 4  # Multi-file, algorithms, architecture
    EXPERT = 5  # Distributed systems, security-critical


class TaskCategory(Enum):
    """Task categories for routing."""

    COMPLETION = "completion"  # Inline code completion
    GENERATION = "generation"  # Write new code
    REFACTOR = "refactor"  # Restructure existing code
    BUG_FIX = "bug_fix"  # Find and fix bugs
    REVIEW = "review"  # Code review
    ARCHITECTURE = "architecture"  # System design
    OPTIMIZATION = "optimization"  # Performance tuning
    TESTING = "testing"  # Write tests
    DOCS = "docs"  # Documentation
    DEBUGGING = "debugging"  # Deep debug sessions


# Model profiles with verified benchmark data (Updated: Feb 2026)
# Ranking strategy:
#   1. FREE models first (multiplier=0) - maximize usage
#   2. CHEAP models (0.25-0.33×) for moderate tasks
#   3. MODERATE models (1×) for complex tasks
#   4. EXPENSIVE models (3-50×) only when absolutely needed
#
# Quality scores based on SWE-Bench, HumanEval, and real-world benchmarks
MODEL_PROFILES: dict[str, dict[str, Any]] = {
    # ─── FREE TIER (Unlimited usage) ───────────────────────────────
    "gpt-4.1": {
        "multiplier": 0,
        "quality_score": 0.89,  # Upgraded: excellent agentic coding
        "speed": 0.90,
        "context_window": 1_047_576,  # ~1M tokens
        "strengths": [Complexity.TRIVIAL, Complexity.SIMPLE, Complexity.MODERATE],
        "categories": [
            TaskCategory.COMPLETION,
            TaskCategory.GENERATION,
            TaskCategory.TESTING,
            TaskCategory.DOCS,
            TaskCategory.REVIEW,
            TaskCategory.REFACTOR,
            TaskCategory.BUG_FIX,
        ],
        "benchmark_note": "Best free model. 97% on easy, 85% on medium. GitHub's default. Agentic coding champion.",
        "tier": "free",
        "rank": 1,
    },
    "gpt-4o": {
        "multiplier": 0,
        "quality_score": 0.86,
        "speed": 0.92,
        "context_window": 128_000,
        "strengths": [Complexity.TRIVIAL, Complexity.SIMPLE, Complexity.MODERATE],
        "categories": [
            TaskCategory.COMPLETION,
            TaskCategory.GENERATION,
            TaskCategory.DOCS,
            TaskCategory.REVIEW,
        ],
        "benchmark_note": "Full vision/multimodal. Use for image-related tasks. Good generalist.",
        "tier": "free",
        "rank": 2,
    },
    "gpt-4.1-mini": {
        "multiplier": 0,
        "quality_score": 0.83,
        "speed": 0.98,
        "context_window": 1_047_576,
        "strengths": [Complexity.TRIVIAL, Complexity.SIMPLE],
        "categories": [TaskCategory.COMPLETION, TaskCategory.DOCS, TaskCategory.GENERATION],
        "benchmark_note": "Fastest free model. Quick edits, prototyping, utility code.",
        "tier": "free",
        "rank": 3,
    },
    # ─── CHEAP TIER (High value) ───────────────────────────────────
    "gemini-2.0-flash": {
        "multiplier": 0.25,
        "quality_score": 0.82,
        "speed": 0.97,
        "context_window": 1_000_000,
        "strengths": [Complexity.TRIVIAL, Complexity.SIMPLE, Complexity.MODERATE],
        "categories": [TaskCategory.COMPLETION, TaskCategory.GENERATION, TaskCategory.DOCS],
        "benchmark_note": "Cheapest premium (0.25×). 1M context. Speed-critical large file tasks.",
        "tier": "cheap",
        "rank": 4,
    },
    "o4-mini": {
        "multiplier": 0.33,
        "quality_score": 0.90,  # Strong reasoning
        "speed": 0.72,
        "context_window": 200_000,
        "strengths": [Complexity.MODERATE, Complexity.COMPLEX],
        "categories": [TaskCategory.DEBUGGING, TaskCategory.OPTIMIZATION, TaskCategory.BUG_FIX],
        "benchmark_note": "Best value for reasoning. Step-by-step logic. Tricky bugs, algorithms.",
        "tier": "cheap",
        "rank": 5,
    },
    "o3-mini": {
        "multiplier": 0.33,
        "quality_score": 0.88,
        "speed": 0.75,
        "context_window": 200_000,
        "strengths": [Complexity.MODERATE, Complexity.COMPLEX],
        "categories": [TaskCategory.DEBUGGING, TaskCategory.BUG_FIX, TaskCategory.TESTING],
        "benchmark_note": "Cost-efficient reasoning. Good for test generation and bug analysis.",
        "tier": "cheap",
        "rank": 6,
    },
    # ─── MODERATE TIER (1× = 300/month) ────────────────────────────
    "claude-sonnet-4": {
        "multiplier": 1.0,
        "quality_score": 0.93,
        "speed": 0.82,
        "context_window": 200_000,
        "strengths": [Complexity.MODERATE, Complexity.COMPLEX],
        "categories": [
            TaskCategory.REFACTOR,
            TaskCategory.ARCHITECTURE,
            TaskCategory.OPTIMIZATION,
            TaskCategory.REVIEW,
            TaskCategory.BUG_FIX,
        ],
        "benchmark_note": "Workhorse for complex tasks. Multi-file refactoring. Strong code review.",
        "tier": "moderate",
        "rank": 7,
    },
    "gemini-2.5-pro": {
        "multiplier": 1.0,
        "quality_score": 0.92,
        "speed": 0.78,
        "context_window": 1_000_000,
        "strengths": [Complexity.COMPLEX, Complexity.EXPERT],
        "categories": [TaskCategory.ARCHITECTURE, TaskCategory.OPTIMIZATION, TaskCategory.REVIEW],
        "benchmark_note": "Massive 1M context. Entire codebase analysis. Architecture decisions.",
        "tier": "moderate",
        "rank": 8,
    },
    # ─── EXPENSIVE TIER (Use sparingly) ────────────────────────────
    "claude-opus-4.5": {
        "multiplier": 3.0,
        "quality_score": 0.97,
        "speed": 0.65,
        "context_window": 200_000,
        "strengths": [Complexity.COMPLEX, Complexity.EXPERT],
        "categories": [TaskCategory.ARCHITECTURE, TaskCategory.DEBUGGING],
        "benchmark_note": "Near-perfect. Complex debugging, critical architecture. 100 uses/month.",
        "tier": "expensive",
        "rank": 9,
    },
    "claude-opus-4": {
        "multiplier": 10.0,
        "quality_score": 0.96,
        "speed": 0.60,
        "context_window": 200_000,
        "strengths": [Complexity.EXPERT],
        "categories": [TaskCategory.ARCHITECTURE],
        "benchmark_note": "10× cost (30 uses/month). Expert-level only. Security audits, migrations.",
        "tier": "expensive",
        "rank": 10,
    },
    # ─── AVOID TIER (Extremely expensive) ──────────────────────────
    "gpt-4.5": {
        "multiplier": 50.0,
        "quality_score": 0.95,
        "speed": 0.55,
        "context_window": 128_000,
        "strengths": [Complexity.EXPERT],
        "categories": [TaskCategory.DEBUGGING],
        "benchmark_note": "50× cost (6 uses/month). AVOID. Only for impossible edge cases.",
        "tier": "avoid",
        "rank": 11,
    },
}

# Complexity detection signals
COMPLEXITY_SIGNALS: dict[Complexity, dict[str, Any]] = {
    Complexity.TRIVIAL: {
        "keywords": [
            "typo",
            "rename",
            "add comment",
            "fix indent",
            "add semicolon",
            "format",
            "whitespace",
            "spelling",
        ],
        "max_files": 1,
        "max_lines_changed": 5,
    },
    Complexity.SIMPLE: {
        "keywords": [
            "add",
            "create function",
            "write",
            "generate",
            "simple",
            "basic",
            "boilerplate",
            "crud",
            "hello world",
            "getter",
            "setter",
            "property",
        ],
        "max_files": 2,
        "max_lines_changed": 50,
    },
    Complexity.MODERATE: {
        "keywords": [
            "refactor",
            "improve",
            "update logic",
            "restructure",
            "connect",
            "integrate",
            "add feature",
            "unit test",
            "validate",
            "sanitize",
            "middleware",
        ],
        "max_files": 5,
        "max_lines_changed": 200,
    },
    Complexity.COMPLEX: {
        "keywords": [
            "architect",
            "design",
            "migrate",
            "multi-file",
            "optimize performance",
            "security audit",
            "refactor all",
            "system",
            "module",
            "service",
            "database schema",
        ],
        "max_files": 20,
        "max_lines_changed": 1000,
    },
    Complexity.EXPERT: {
        "keywords": [
            "distributed",
            "microservices",
            "real-time",
            "scalability",
            "zero-downtime",
            "critical path",
            "consensus",
            "sharding",
            "security critical",
            "compliance",
            "fault-tolerant",
        ],
        "max_files": 999,
        "max_lines_changed": 99999,
    },
}

# Category detection keywords
CATEGORY_KEYWORDS: dict[TaskCategory, list[str]] = {
    TaskCategory.BUG_FIX: ["fix", "bug", "broken", "error", "crash", "failing", "wrong"],
    TaskCategory.REFACTOR: ["refactor", "restructure", "clean up", "reorganize", "simplify"],
    TaskCategory.TESTING: ["test", "spec", "unit test", "integration test", "coverage"],
    TaskCategory.DOCS: ["document", "readme", "comment", "jsdoc", "docstring", "explain"],
    TaskCategory.ARCHITECTURE: ["architect", "design", "system", "plan", "structure", "schema"],
    TaskCategory.OPTIMIZATION: ["optimize", "performance", "speed up", "slow", "memory", "cache"],
    TaskCategory.DEBUGGING: ["debug", "why", "trace", "log", "inspect", "investigate"],
    TaskCategory.REVIEW: ["review", "check", "audit", "validate", "analyze"],
    TaskCategory.GENERATION: ["create", "write", "generate", "build", "implement", "add"],
    TaskCategory.COMPLETION: ["complete", "finish", "suggest", "next", "continue"],
}


@dataclass
class RoutingDecision:
    """Result of task routing analysis."""

    model: str
    complexity: Complexity
    category: TaskCategory
    multiplier: float
    effective_multiplier: float  # After auto-mode discount
    reasoning: str
    fallback_chain: list[str]
    premium_requests_cost: float
    quality_boosters: list[str]

    @property
    def is_free(self) -> bool:
        return self.multiplier == 0

    @property
    def is_expensive(self) -> bool:
        return self.multiplier >= 3.0


class BudgetTracker:
    """Tracks premium request budget usage."""

    def __init__(self, monthly_limit: int = 300):
        self.monthly_limit = monthly_limit
        self.used: float = 0.0
        self._history: list[dict[str, Any]] = []

    def can_afford(self, multiplier: float) -> bool:
        """Check if budget allows this request."""
        return (self.used + multiplier) <= self.monthly_limit

    def consume(self, multiplier: float, model: str = "") -> None:
        """Record budget consumption."""
        self.used += multiplier
        self._history.append({"multiplier": multiplier, "model": model, "running_total": self.used})

    @property
    def remaining(self) -> float:
        return self.monthly_limit - self.used

    @property
    def usage_pct(self) -> float:
        return (self.used / self.monthly_limit) * 100

    def reset(self) -> None:
        """Reset budget (e.g., at month start)."""
        self.used = 0.0
        self._history.clear()


class AdaptiveLearner:
    """Learns optimal model selection from usage patterns."""

    def __init__(self, min_samples: int = 5):
        self.min_samples = min_samples
        self._history: list[dict[str, Any]] = []

    def record(
        self,
        complexity: Complexity,
        category: TaskCategory,
        model: str,
        success: bool,
        user_feedback: str | None = None,
    ) -> None:
        """Record a task execution result."""
        self._history.append(
            {
                "complexity": complexity,
                "category": category,
                "model": model,
                "success": success,
                "feedback": user_feedback,
            }
        )

    def get_best_model(self, complexity: Complexity, category: TaskCategory) -> str | None:
        """Get the best model for this task type based on history."""
        relevant = [
            h for h in self._history if h["complexity"] == complexity and h["category"] == category
        ]

        if len(relevant) < self.min_samples:
            return None

        # Group by model, compute success rate
        model_scores: dict[str, list[bool]] = {}
        for h in relevant:
            model_scores.setdefault(h["model"], []).append(h["success"])

        best_model = None
        best_rate = 0.0

        for model, results in model_scores.items():
            rate = sum(results) / len(results)
            if rate > best_rate and rate > 0.85:
                best_rate = rate
                best_model = model

        return best_model


class TaskRouter:
    """
    Intelligent task routing engine.

    Routes tasks to the optimal model based on complexity,
    category, budget, and learned preferences.

    Example:
        >>> router = TaskRouter()
        >>> decision = router.route("fix the authentication bug in auth.js")
        >>> print(f"Use {decision.model} (cost: {decision.multiplier}×)")
    """

    def __init__(self, config: RouterConfig | None = None):
        self.config = config or RouterConfig()
        self.budget = BudgetTracker(self.config.monthly_premium_limit)
        self.learner = AdaptiveLearner(self.config.min_samples_for_learning)

    def route(self, request: str, workspace: dict[str, Any] | None = None) -> RoutingDecision:
        """
        Route a task to the optimal model.

        Args:
            request: The user's task description
            workspace: Optional workspace context (affected files, etc.)

        Returns:
            RoutingDecision with model selection and reasoning
        """
        workspace = workspace or {}

        # Detect complexity
        complexity = self._detect_complexity(request, workspace)

        # Detect category
        category = self._detect_category(request)

        # Get candidate models
        candidates = self._get_candidates(complexity, category)

        # Check learned preferences
        if self.config.adaptive_learning_enabled:
            learned = self.learner.get_best_model(complexity, category)
            if learned and learned in candidates:
                candidates.insert(0, learned)

        # Select optimal model using smart scoring
        selected = self._select_optimal(candidates, complexity, category)

        # Get quality boosters
        boosters = self._get_boosters(selected, complexity, category)

        # Build fallback chain
        fallbacks = [m for m in candidates if m != selected][:3]

        # Calculate effective multiplier with auto discount
        profile = MODEL_PROFILES[selected]
        effective = self._calc_effective(selected)

        return RoutingDecision(
            model=selected,
            complexity=complexity,
            category=category,
            multiplier=profile["multiplier"],
            effective_multiplier=effective,
            reasoning=self._explain(selected, complexity, category),
            fallback_chain=fallbacks,
            premium_requests_cost=profile["multiplier"],
            quality_boosters=boosters,
        )

    def _detect_complexity(self, request: str, workspace: dict[str, Any]) -> Complexity:
        """Detect task complexity from request and context."""
        request_lower = request.lower()
        file_count = workspace.get("affected_files", 1)

        # Score each complexity level
        scores: dict[Complexity, int] = {}
        for level, signals in COMPLEXITY_SIGNALS.items():
            keyword_hits = sum(1 for kw in signals["keywords"] if kw in request_lower)
            scores[level] = keyword_hits

        # Scope override based on file count
        if file_count >= 20:
            return Complexity.COMPLEX
        if file_count >= 5:
            # Floor at MODERATE for 5+ files
            best = max(scores, key=lambda k: scores[k])
            if best.value < Complexity.MODERATE.value:
                return Complexity.MODERATE
            return best

        # Return highest scoring level
        if scores:
            best = max(scores, key=lambda k: scores[k])
            if scores[best] > 0:
                return best

        return Complexity.SIMPLE

    def _detect_category(self, request: str) -> TaskCategory:
        """Detect task category from request."""
        request_lower = request.lower()

        best_category = TaskCategory.GENERATION
        best_score = 0

        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in request_lower)
            if score > best_score:
                best_score = score
                best_category = cat

        return best_category

    def _get_candidates(self, complexity: Complexity, category: TaskCategory) -> list[str]:
        """
        Get candidate models using smart ranking strategy.

        Strategy:
        1. Filter by capability (complexity + category match)
        2. Exclude "avoid" tier unless EXPERT complexity
        3. Sort by: tier priority → rank within tier → cost
        """
        tier_priority = {"free": 0, "cheap": 1, "moderate": 2, "expensive": 3, "avoid": 4}
        candidates = []

        for name, profile in MODEL_PROFILES.items():
            # Skip "avoid" tier unless absolutely needed
            if profile.get("tier") == "avoid" and complexity != Complexity.EXPERT:
                continue

            # Check capability match
            can_handle_complexity = complexity in profile["strengths"]
            can_handle_category = category in profile["categories"]

            if can_handle_complexity or can_handle_category:
                candidates.append(name)

        # Smart sort: tier priority first, then rank within tier
        candidates.sort(
            key=lambda m: (
                tier_priority.get(MODEL_PROFILES[m].get("tier", "moderate"), 2),
                MODEL_PROFILES[m].get("rank", 99),
                MODEL_PROFILES[m]["multiplier"],
            )
        )

        # Ensure at least one candidate
        if not candidates:
            candidates = ["gpt-4.1"]

        return candidates

    def _select_optimal(
        self, candidates: list[str], complexity: Complexity, category: TaskCategory | None = None
    ) -> str:
        """
        Select optimal model balancing QUALITY and COST based on complexity.

        Strategy:
        - TRIVIAL/SIMPLE: Maximize cost savings (free models preferred)
        - MODERATE: Balance quality and cost (value optimization)
        - COMPLEX/EXPERT: Prioritize quality (best model affordable)

        "Quality of work matters" - don't sacrifice results for savings.
        """
        # Quality thresholds per complexity
        thresholds = {
            Complexity.TRIVIAL: self.config.trivial_quality_threshold,
            Complexity.SIMPLE: self.config.simple_quality_threshold,
            Complexity.MODERATE: self.config.moderate_quality_threshold,
            Complexity.COMPLEX: self.config.complex_quality_threshold,
            Complexity.EXPERT: self.config.expert_quality_threshold,
        }
        threshold = thresholds.get(complexity, 0.85)

        # For COMPLEX/EXPERT tasks: prioritize quality over cost
        # Select the HIGHEST quality model we can afford
        if complexity in [Complexity.COMPLEX, Complexity.EXPERT]:
            return self._select_highest_quality(candidates, threshold)

        # For TRIVIAL/SIMPLE: prioritize cost savings
        # Select cheapest model that meets threshold
        if complexity in [Complexity.TRIVIAL, Complexity.SIMPLE]:
            return self._select_cheapest_adequate(candidates, threshold)

        # For MODERATE: balance quality and cost with value scoring
        return self._select_best_value(candidates, threshold, complexity)

    def _select_highest_quality(self, candidates: list[str], min_threshold: float) -> str:
        """Select highest quality model we can afford. Quality > Cost."""
        best_model = None
        best_quality = 0.0

        for model in candidates:
            profile = MODEL_PROFILES[model]
            quality = profile["quality_score"]

            # Must meet threshold and budget
            if quality < min_threshold:
                continue
            if not self.budget.can_afford(profile["multiplier"]):
                continue

            # Pick highest quality
            if quality > best_quality:
                best_quality = quality
                best_model = model

        return best_model or candidates[0] if candidates else "gpt-4.1"

    def _select_cheapest_adequate(self, candidates: list[str], min_threshold: float) -> str:
        """Select cheapest model meeting threshold. Cost > Quality."""
        # Candidates already sorted by cost, pick first adequate one
        for model in candidates:
            profile = MODEL_PROFILES[model]
            if profile["quality_score"] >= min_threshold:
                if self.budget.can_afford(profile["multiplier"]):
                    return model

        return candidates[0] if candidates else "gpt-4.1"

    def _select_best_value(
        self, candidates: list[str], min_threshold: float, complexity: Complexity
    ) -> str:
        """Select best value model (quality-adjusted cost). Balanced approach."""
        scored_candidates: list[tuple[str, float]] = []

        for model in candidates:
            profile = MODEL_PROFILES[model]
            quality = profile["quality_score"]

            # Must meet threshold and budget
            if quality < min_threshold:
                continue
            if not self.budget.can_afford(profile["multiplier"]):
                continue

            # Value score: quality^2 / cost (quality weighted more)
            cost = max(profile["multiplier"], 0.1)
            value_score = (quality**2) / cost

            # Tier adjustments (less aggressive than before)
            tier = profile.get("tier", "moderate")
            if tier == "free":
                value_score *= 2.0  # Moderate bonus for free
            elif tier == "cheap":
                value_score *= 1.5  # Small bonus for cheap
            elif tier == "expensive":
                value_score *= 0.8  # Slight penalty
            elif tier == "avoid":
                value_score *= 0.3  # Strong penalty

            # Context window bonus for large files
            if profile["context_window"] >= 500_000:
                value_score *= 1.1

            scored_candidates.append((model, value_score))

        if scored_candidates:
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            return scored_candidates[0][0]

        return candidates[0] if candidates else "gpt-4.1"

    def _calc_effective(self, model: str) -> float:
        """Calculate effective multiplier with auto-mode discount."""
        base = MODEL_PROFILES[model]["multiplier"]

        if base == 0:
            return 0.0

        if self.config.use_auto_mode_discount:
            return round(base * (1 - self.config.auto_mode_discount_rate), 2)

        return base

    def _get_boosters(
        self, model: str, complexity: Complexity, category: TaskCategory
    ) -> list[str]:
        """
        Get quality boosters needed for this combination.

        Boosters enhance cheaper models to produce premium output.
        """
        boosters = []
        profile = MODEL_PROFILES[model]

        # Quality demand per complexity
        quality_demand = {
            Complexity.TRIVIAL: 0.80,
            Complexity.SIMPLE: 0.82,
            Complexity.MODERATE: 0.88,
            Complexity.COMPLEX: 0.93,
            Complexity.EXPERT: 0.97,
        }

        # Add boosters if model quality < demand
        if profile["quality_score"] < quality_demand.get(complexity, 0.85):
            boosters.append("expert_role_framing")
            boosters.append("chain_of_thought_injection")

        if complexity in [Complexity.COMPLEX, Complexity.EXPERT]:
            boosters.append("few_shot_examples")
            boosters.append("structured_output_enforcement")

        if category in [TaskCategory.BUG_FIX, TaskCategory.DEBUGGING]:
            boosters.append("step_by_step_reasoning")

        if category == TaskCategory.ARCHITECTURE:
            boosters.append("tradeoff_analysis_prompt")

        # Always validate code output
        boosters.append("post_validation")

        return boosters

    def _explain(self, model: str, complexity: Complexity, category: TaskCategory) -> str:
        """Generate human-readable routing explanation."""
        profile = MODEL_PROFILES[model]
        return (
            f"Task: {category.value} | Complexity: {complexity.name} | "
            f"Selected: {model} (quality: {profile['quality_score']}, "
            f"multiplier: {profile['multiplier']}×) | "
            f"Note: {profile['benchmark_note']}"
        )

    def record_result(
        self, decision: RoutingDecision, success: bool, feedback: str | None = None
    ) -> None:
        """Record task result for adaptive learning."""
        # Update budget
        self.budget.consume(decision.effective_multiplier, decision.model)

        # Record for learning
        if self.config.adaptive_learning_enabled:
            self.learner.record(
                decision.complexity, decision.category, decision.model, success, feedback
            )
