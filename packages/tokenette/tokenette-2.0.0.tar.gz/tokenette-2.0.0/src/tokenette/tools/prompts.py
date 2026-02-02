"""
Prompt Templates & Engineering Tools

Pre-built, optimized prompts for common coding tasks.
Reduces token overhead and improves model output quality.
"""

from dataclasses import dataclass
from enum import Enum


class PromptCategory(Enum):
    """Categories of prompt templates."""

    CODE_GENERATION = "code_generation"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REVIEW = "review"
    ARCHITECTURE = "architecture"
    OPTIMIZATION = "optimization"


@dataclass
class PromptTemplate:
    """A reusable prompt template."""

    name: str
    category: PromptCategory
    template: str
    description: str
    variables: list[str]
    example_output: str = ""
    token_estimate: int = 0


@dataclass
class BuiltPrompt:
    """A built prompt ready for use."""

    prompt: str
    template_name: str
    variables_used: dict[str, str]
    token_count: int
    quality_boosters: list[str]


# ─── PROMPT TEMPLATES ────────────────────────────────────────────

TEMPLATES: dict[str, PromptTemplate] = {
    # Code Generation
    "function": PromptTemplate(
        name="function",
        category=PromptCategory.CODE_GENERATION,
        template="""Write a {language} function:
Name: {name}
Purpose: {purpose}
Parameters: {params}
Returns: {returns}
Requirements:
- Production-ready with error handling
- Include type hints/annotations
- Follow {language} best practices""",
        description="Generate a well-structured function",
        variables=["language", "name", "purpose", "params", "returns"],
        token_estimate=80,
    ),
    "class": PromptTemplate(
        name="class",
        category=PromptCategory.CODE_GENERATION,
        template="""Design a {language} class:
Name: {name}
Purpose: {purpose}
Key Methods: {methods}
Properties: {properties}
Requirements:
- Clean architecture, single responsibility
- Proper encapsulation
- Include docstrings/comments""",
        description="Generate a well-designed class",
        variables=["language", "name", "purpose", "methods", "properties"],
        token_estimate=90,
    ),
    "api_endpoint": PromptTemplate(
        name="api_endpoint",
        category=PromptCategory.CODE_GENERATION,
        template="""Create a {framework} API endpoint:
Method: {method}
Path: {path}
Purpose: {purpose}
Request Body: {request_body}
Response: {response}
Requirements:
- Input validation
- Error handling with proper status codes
- Authentication/authorization if needed""",
        description="Generate a REST API endpoint",
        variables=["framework", "method", "path", "purpose", "request_body", "response"],
        token_estimate=100,
    ),
    # Refactoring
    "refactor_function": PromptTemplate(
        name="refactor_function",
        category=PromptCategory.REFACTORING,
        template="""Refactor this {language} function:

```{language}
{code}
```

Goals:
- {goals}

Constraints:
- Maintain existing behavior (no breaking changes)
- Improve readability and maintainability
- Follow {language} idioms and best practices

Output the refactored code with brief explanation of changes.""",
        description="Refactor a function with specific goals",
        variables=["language", "code", "goals"],
        token_estimate=120,
    ),
    "extract_method": PromptTemplate(
        name="extract_method",
        category=PromptCategory.REFACTORING,
        template="""Extract a method from this code:

```{language}
{code}
```

Lines to extract: {lines}
New method name: {method_name}
Purpose: {purpose}

Requirements:
- Identify parameters needed
- Determine return value
- Update calling code
- Preserve all functionality""",
        description="Extract code into a separate method",
        variables=["language", "code", "lines", "method_name", "purpose"],
        token_estimate=100,
    ),
    # Debugging
    "find_bug": PromptTemplate(
        name="find_bug",
        category=PromptCategory.DEBUGGING,
        template="""Debug this {language} code:

```{language}
{code}
```

Symptoms: {symptoms}
Expected: {expected}
Actual: {actual}

Analyze step by step:
1. Identify the root cause
2. Explain why the bug occurs
3. Provide the fix
4. Suggest how to prevent similar bugs""",
        description="Find and fix a bug with detailed analysis",
        variables=["language", "code", "symptoms", "expected", "actual"],
        token_estimate=130,
    ),
    "trace_execution": PromptTemplate(
        name="trace_execution",
        category=PromptCategory.DEBUGGING,
        template="""Trace the execution of this code:

```{language}
{code}
```

Input: {input}

Walk through line by line:
- Show variable values at each step
- Identify where behavior diverges from expected
- Point out any issues found""",
        description="Step-by-step execution trace",
        variables=["language", "code", "input"],
        token_estimate=100,
    ),
    # Testing
    "unit_tests": PromptTemplate(
        name="unit_tests",
        category=PromptCategory.TESTING,
        template="""Write unit tests for this {language} code:

```{language}
{code}
```

Testing framework: {framework}
Coverage goals:
- Happy path cases
- Edge cases: {edge_cases}
- Error cases: {error_cases}

Requirements:
- Descriptive test names
- Arrange-Act-Assert pattern
- Independent, isolated tests""",
        description="Generate comprehensive unit tests",
        variables=["language", "code", "framework", "edge_cases", "error_cases"],
        token_estimate=140,
    ),
    "test_cases": PromptTemplate(
        name="test_cases",
        category=PromptCategory.TESTING,
        template="""Generate test cases for: {feature}

Context: {context}

Generate:
1. 5 happy path test cases
2. 5 edge case scenarios
3. 3 error/failure scenarios

Format: | Test Name | Input | Expected Output | Type |""",
        description="Generate test case matrix",
        variables=["feature", "context"],
        token_estimate=80,
    ),
    # Documentation
    "docstring": PromptTemplate(
        name="docstring",
        category=PromptCategory.DOCUMENTATION,
        template="""Write a comprehensive docstring for:

```{language}
{code}
```

Style: {style}
Include:
- Brief description
- Args/Parameters with types
- Returns with type
- Raises/Exceptions
- Example usage""",
        description="Generate function/class documentation",
        variables=["language", "code", "style"],
        token_estimate=90,
    ),
    "readme_section": PromptTemplate(
        name="readme_section",
        category=PromptCategory.DOCUMENTATION,
        template="""Write a README section for: {section}

Project: {project_name}
Context: {context}

Tone: Professional, clear, concise
Include: {include}
Format: Markdown with code examples""",
        description="Generate README documentation",
        variables=["section", "project_name", "context", "include"],
        token_estimate=70,
    ),
    # Code Review
    "code_review": PromptTemplate(
        name="code_review",
        category=PromptCategory.REVIEW,
        template="""Review this {language} code:

```{language}
{code}
```

Focus areas: {focus}

Provide feedback on:
1. **Correctness**: Logic errors, bugs
2. **Security**: Vulnerabilities, unsafe practices
3. **Performance**: Inefficiencies, bottlenecks
4. **Maintainability**: Readability, complexity
5. **Best Practices**: Language idioms, patterns

Format: Severity (🔴Critical/🟡Warning/🔵Info) | Line | Issue | Suggestion""",
        description="Comprehensive code review",
        variables=["language", "code", "focus"],
        token_estimate=150,
    ),
    "security_audit": PromptTemplate(
        name="security_audit",
        category=PromptCategory.REVIEW,
        template="""Security audit for this {language} code:

```{language}
{code}
```

Check for:
- Injection vulnerabilities (SQL, XSS, command)
- Authentication/authorization issues
- Sensitive data exposure
- Insecure configurations
- Dependency vulnerabilities

OWASP Top 10 focus: {owasp_focus}

Format: Severity | CWE ID | Issue | Location | Remediation""",
        description="Security-focused code audit",
        variables=["language", "code", "owasp_focus"],
        token_estimate=140,
    ),
    # Architecture
    "design_pattern": PromptTemplate(
        name="design_pattern",
        category=PromptCategory.ARCHITECTURE,
        template="""Implement the {pattern} pattern in {language}:

Context: {context}
Classes involved: {classes}

Requirements:
- Clean, idiomatic implementation
- Include interface/abstract classes
- Show usage example
- Explain when to use this pattern""",
        description="Implement a design pattern",
        variables=["pattern", "language", "context", "classes"],
        token_estimate=100,
    ),
    "system_design": PromptTemplate(
        name="system_design",
        category=PromptCategory.ARCHITECTURE,
        template="""Design a system for: {requirement}

Constraints:
- Scale: {scale}
- Latency: {latency}
- Availability: {availability}

Provide:
1. High-level architecture diagram (text-based)
2. Component breakdown
3. Data flow
4. Technology choices with justification
5. Scalability considerations
6. Potential bottlenecks and mitigations""",
        description="System design document",
        variables=["requirement", "scale", "latency", "availability"],
        token_estimate=160,
    ),
    # Optimization
    "optimize_performance": PromptTemplate(
        name="optimize_performance",
        category=PromptCategory.OPTIMIZATION,
        template="""Optimize this {language} code for performance:

```{language}
{code}
```

Current issues: {issues}
Target metric: {metric}

Analyze:
1. Time complexity
2. Space complexity
3. I/O operations
4. Memory allocations

Provide optimized version with:
- Benchmarks comparison
- Tradeoffs explained""",
        description="Performance optimization",
        variables=["language", "code", "issues", "metric"],
        token_estimate=140,
    ),
    "reduce_complexity": PromptTemplate(
        name="reduce_complexity",
        category=PromptCategory.OPTIMIZATION,
        template="""Reduce complexity of this code:

```{language}
{code}
```

Current complexity: {current_complexity}
Target: Reduce to {target_complexity}

Techniques to consider:
- Algorithm optimization
- Data structure changes
- Early termination
- Caching/memoization
- Divide and conquer""",
        description="Reduce algorithmic complexity",
        variables=["language", "code", "current_complexity", "target_complexity"],
        token_estimate=100,
    ),
}


class PromptBuilder:
    """Build and manage prompt templates."""

    def __init__(self):
        self.templates = TEMPLATES.copy()
        self.custom_templates: dict[str, PromptTemplate] = {}

    def list_templates(self, category: PromptCategory | None = None) -> list[dict[str, str]]:
        """List available templates."""
        result = []

        for name, template in self.templates.items():
            if category and template.category != category:
                continue

            result.append(
                {
                    "name": name,
                    "category": template.category.value,
                    "description": template.description,
                    "variables": template.variables,
                }
            )

        return result

    def get_template(self, name: str) -> PromptTemplate | None:
        """Get a template by name."""
        return self.templates.get(name) or self.custom_templates.get(name)

    def build(
        self,
        template_name: str,
        variables: dict[str, str],
        quality_boosters: list[str] | None = None,
    ) -> BuiltPrompt:
        """
        Build a prompt from a template.

        Args:
            template_name: Name of the template
            variables: Variable values to fill in
            quality_boosters: Optional boosters to prepend

        Returns:
            BuiltPrompt ready for use
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")

        # Fill in variables
        prompt = template.template
        for var in template.variables:
            value = variables.get(var, f"[{var}]")
            prompt = prompt.replace(f"{{{var}}}", value)

        # Add quality boosters
        boosters = quality_boosters or []
        if boosters:
            booster_text = self._build_boosters(boosters)
            prompt = booster_text + "\n\n" + prompt

        token_count = len(prompt) // 4  # Approximate

        return BuiltPrompt(
            prompt=prompt,
            template_name=template_name,
            variables_used=variables,
            token_count=token_count,
            quality_boosters=boosters,
        )

    def _build_boosters(self, boosters: list[str]) -> str:
        """Build booster prefix text."""
        booster_texts = {
            "expert_role_framing": "You are a senior software engineer with 15+ years of experience.",
            "chain_of_thought_injection": "Think through this step by step before providing your answer.",
            "step_by_step_reasoning": "Reason through each step carefully, showing your work.",
            "few_shot_examples": "Follow the examples provided closely.",
            "structured_output_enforcement": "Structure your response clearly with sections.",
            "tradeoff_analysis_prompt": "Consider tradeoffs and explain your choices.",
            "post_validation": "Verify your solution is correct before presenting it.",
        }

        return " ".join(booster_texts.get(b, "") for b in boosters if b in booster_texts)

    def add_custom_template(
        self,
        name: str,
        template: str,
        category: PromptCategory,
        description: str,
        variables: list[str],
    ) -> PromptTemplate:
        """Add a custom template."""
        new_template = PromptTemplate(
            name=name,
            category=category,
            template=template,
            description=description,
            variables=variables,
            token_estimate=len(template) // 4,
        )
        self.custom_templates[name] = new_template
        return new_template


# Singleton instance
_prompt_builder: PromptBuilder | None = None


def get_prompt_builder() -> PromptBuilder:
    """Get the prompt builder singleton."""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder


def build_prompt(
    template_name: str, variables: dict[str, str], quality_boosters: list[str] | None = None
) -> BuiltPrompt:
    """Convenience function to build a prompt."""
    return get_prompt_builder().build(template_name, variables, quality_boosters)


def list_templates(category: str | None = None) -> list[dict[str, str]]:
    """Convenience function to list templates."""
    cat = PromptCategory(category) if category else None
    return get_prompt_builder().list_templates(cat)
