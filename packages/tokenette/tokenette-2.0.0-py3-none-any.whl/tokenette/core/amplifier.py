"""
Quality Amplification Engine

Makes cheaper models produce premium-quality output by:
- Expert role framing
- Chain of thought injection
- Few-shot examples
- Structured output enforcement
- Tradeoff analysis prompts

Applied BEFORE the request hits the model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tokenette.config import AmplifierConfig
from tokenette.core.router import TaskCategory


@dataclass
class AmplificationResult:
    """Result of prompt amplification."""

    prompt: str
    original_length: int
    amplified_length: int
    boosters_applied: list[str]

    @property
    def overhead_tokens(self) -> int:
        """Extra tokens added by amplification."""
        return (self.amplified_length - self.original_length) // 4


class QualityAmplifier:
    """
    Makes cheaper models produce premium-quality output.

    Applies enhancement techniques before the prompt hits the model:
    - Role framing: "You are a senior software engineer..."
    - Chain of thought: "Think step by step..."
    - Few-shot examples: Show examples of desired output
    - Structured output: Enforce consistent response format
    - Tradeoff analysis: Consider alternatives before deciding

    Example:
        >>> amplifier = QualityAmplifier()
        >>> result = amplifier.amplify(
        ...     prompt="fix the auth bug",
        ...     boosters=["expert_role_framing", "chain_of_thought_injection"],
        ...     category=TaskCategory.BUG_FIX
        ... )
        >>> print(result.prompt)
    """

    # Expert role frames per category
    ROLE_FRAMES = {
        TaskCategory.GENERATION: (
            "You are a senior software engineer with 15+ years of experience "
            "writing production-grade code. You write clean, maintainable, "
            "and well-documented code following industry best practices."
        ),
        TaskCategory.ARCHITECTURE: (
            "You are a principal architect specializing in scalable, resilient "
            "system design. You consider trade-offs carefully and design for "
            "maintainability, performance, and future extensibility."
        ),
        TaskCategory.BUG_FIX: (
            "You are an expert debugger with deep knowledge of common bug patterns. "
            "You reason step by step before proposing any fix, always considering "
            "edge cases and potential side effects."
        ),
        TaskCategory.OPTIMIZATION: (
            "You are a performance optimization specialist. You profile mentally "
            "before suggesting changes, understanding the actual bottlenecks and "
            "avoiding premature optimization."
        ),
        TaskCategory.REVIEW: (
            "You are a code reviewer at a top-tier tech company. You are thorough "
            "but constructive, focusing on correctness, maintainability, security, "
            "and performance in that order."
        ),
        TaskCategory.TESTING: (
            "You are a QA engineer obsessed with edge cases and coverage. You write "
            "tests that are maintainable, fast, and actually catch bugs. You focus "
            "on testing behavior, not implementation."
        ),
        TaskCategory.DEBUGGING: (
            "You are a debugging specialist. You trace execution paths systematically, "
            "form hypotheses, and validate them with evidence before drawing conclusions."
        ),
        TaskCategory.DOCS: (
            "You are a technical writer who values precision and clarity. You write "
            "documentation that is accurate, concise, and includes practical examples."
        ),
        TaskCategory.REFACTOR: (
            "You are a clean-code specialist. You prioritize readability, maintainability, "
            "and SOLID principles. You refactor incrementally and always ensure the "
            "refactored code is testable."
        ),
        TaskCategory.COMPLETION: (
            "Complete the code naturally, matching the existing style exactly. "
            "Maintain consistency with the surrounding codebase."
        ),
    }

    # Structured output template
    STRUCTURED_OUTPUT_TEMPLATE = """
Output your response in this exact structure:
1. ANALYSIS: What the code/task actually needs (2-3 sentences max)
2. APPROACH: Your chosen strategy and why (1-2 sentences)
3. CODE: The implementation (clean, production-ready)
4. VERIFICATION: How to confirm it works (test command or check)
"""

    # Chain of thought prefix
    CHAIN_OF_THOUGHT_PREFIX = (
        "Think through this step by step before writing any code. "
        "Identify edge cases, dependencies, and potential failure points first.\n\n"
    )

    # Tradeoff analysis template
    TRADEOFF_TEMPLATE = """
Before designing, briefly consider:
- What are 2-3 alternative approaches?
- What are the tradeoffs (performance vs. complexity vs. maintainability)?
- Which tradeoff is best for this context and why?
Then proceed with the best approach.
"""

    # Few-shot examples per category
    FEW_SHOT_EXAMPLES = {
        TaskCategory.BUG_FIX: (
            "Example: Bug in auth middleware\n"
            "Analysis: Token validation skips expiry check on refresh tokens\n"
            "Fix: Added `exp` claim verification before accepting refresh\n"
            "Verification: `npm test -- --grep 'refresh token expiry'`\n"
            "---"
        ),
        TaskCategory.REFACTOR: (
            "Example: Refactor user service\n"
            "Analysis: God-class with 15 methods mixing concerns\n"
            "Approach: Extract auth, profile, and notification into separate modules\n"
            "Result: Each module <50 lines, single responsibility\n"
            "---"
        ),
        TaskCategory.ARCHITECTURE: (
            "Example: Design notification system\n"
            "Tradeoffs: WebSocket (real-time, complex) vs. Polling (simple, latency)\n"
            "Decision: Event queue + WebSocket for real-time, fallback to SSE\n"
            "Result: <200ms delivery, handles 10K concurrent connections\n"
            "---"
        ),
        TaskCategory.TESTING: (
            "Example: Test authentication flow\n"
            "Analysis: Need to test login, token refresh, and logout\n"
            "Approach: Use test fixtures, mock external auth provider\n"
            "Coverage: Happy path, expired token, invalid credentials, rate limiting\n"
            "---"
        ),
        TaskCategory.OPTIMIZATION: (
            "Example: Slow database queries\n"
            "Analysis: N+1 query pattern in user list endpoint\n"
            "Approach: Add eager loading with proper indices\n"
            "Result: Query time reduced from 2.3s to 45ms\n"
            "---"
        ),
    }

    # Step-by-step reasoning template
    STEP_BY_STEP_TEMPLATE = """
Work through this systematically:
1. First, understand the current state and the exact problem
2. Then, identify the root cause (not just symptoms)
3. Next, consider potential solutions and their trade-offs
4. Finally, implement the best solution with minimal side effects
"""

    def __init__(self, config: AmplifierConfig | None = None):
        self.config = config or AmplifierConfig()

    def amplify(
        self,
        prompt: str,
        boosters: list[str],
        category: TaskCategory,
        context: dict[str, Any] | None = None,
    ) -> AmplificationResult:
        """
        Amplify a prompt with quality-enhancing techniques.

        Args:
            prompt: Original user prompt
            boosters: List of boosters to apply
            category: Task category for appropriate framing
            context: Optional additional context

        Returns:
            AmplificationResult with enhanced prompt
        """
        original_length = len(prompt)
        enhanced = prompt
        applied = []

        # Apply boosters in order
        if "expert_role_framing" in boosters and self.config.use_role_framing:
            role = self.ROLE_FRAMES.get(category, self.ROLE_FRAMES[TaskCategory.GENERATION])
            enhanced = f"{role}\n\n{enhanced}"
            applied.append("expert_role_framing")

        if "chain_of_thought_injection" in boosters and self.config.use_chain_of_thought:
            enhanced = self.CHAIN_OF_THOUGHT_PREFIX + enhanced
            applied.append("chain_of_thought_injection")

        if "step_by_step_reasoning" in boosters and self.config.use_chain_of_thought:
            enhanced = self.STEP_BY_STEP_TEMPLATE + "\n\n" + enhanced
            applied.append("step_by_step_reasoning")

        if "tradeoff_analysis_prompt" in boosters and self.config.use_tradeoff_analysis:
            enhanced = self.TRADEOFF_TEMPLATE + "\n\n" + enhanced
            applied.append("tradeoff_analysis_prompt")

        if "few_shot_examples" in boosters and self.config.use_few_shot_examples:
            examples = self.FEW_SHOT_EXAMPLES.get(category, "")
            if examples:
                enhanced = examples + "\n\nNow handle this task:\n\n" + enhanced
                applied.append("few_shot_examples")

        if "structured_output_enforcement" in boosters and self.config.use_structured_output:
            enhanced = enhanced + "\n\n" + self.STRUCTURED_OUTPUT_TEMPLATE
            applied.append("structured_output_enforcement")

        # Post-validation instruction
        if "post_validation" in boosters and self.config.post_validation_enabled:
            enhanced += "\n\nBefore submitting, verify your solution handles edge cases and follows best practices."
            applied.append("post_validation")

        return AmplificationResult(
            prompt=enhanced,
            original_length=original_length,
            amplified_length=len(enhanced),
            boosters_applied=applied,
        )

    def get_validation_prompt(self, code: str, category: TaskCategory) -> str:
        """
        Generate a validation prompt for post-processing.

        This can be used to validate model output before returning.
        """
        validation_prompts = {
            TaskCategory.BUG_FIX: (
                "Review this fix for:\n"
                "- Does it address the root cause?\n"
                "- Are there any edge cases missed?\n"
                "- Could it introduce new bugs?\n"
            ),
            TaskCategory.GENERATION: (
                "Review this code for:\n"
                "- Is it production-ready?\n"
                "- Are there any security issues?\n"
                "- Does it handle errors properly?\n"
            ),
            TaskCategory.REFACTOR: (
                "Review this refactoring for:\n"
                "- Is it a pure refactoring (no behavior change)?\n"
                "- Is it actually simpler/cleaner?\n"
                "- Is it testable?\n"
            ),
        }

        base_prompt = validation_prompts.get(
            category, "Review this code for correctness and best practices:\n"
        )

        return f"{base_prompt}\n```\n{code}\n```"

    def estimate_quality_improvement(self, boosters: list[str], base_quality: float) -> float:
        """
        Estimate quality improvement from boosters.

        Each booster provides a multiplicative improvement.
        """
        improvement_factors = {
            "expert_role_framing": 1.05,
            "chain_of_thought_injection": 1.08,
            "step_by_step_reasoning": 1.10,
            "tradeoff_analysis_prompt": 1.06,
            "few_shot_examples": 1.12,
            "structured_output_enforcement": 1.07,
            "post_validation": 1.03,
        }

        improved = base_quality
        for booster in boosters:
            factor = improvement_factors.get(booster, 1.0)
            improved = min(1.0, improved * factor)

        return round(improved, 3)
