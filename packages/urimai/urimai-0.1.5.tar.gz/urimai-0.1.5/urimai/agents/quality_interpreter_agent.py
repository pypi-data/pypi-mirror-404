"""Quality Interpretation Agent - Interprets results in business context."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from urimai.utils.llm import get_model
from urimai.agents.schema_context_agent import DatabaseContext
from urimai.agents.quality_generation_agent import QualityCheck


class Finding(BaseModel):
    """A quality finding with business context."""

    issue: str = Field(description="Description of the quality issue")
    business_impact: str = Field(
        description="Why this matters for the business/domain"
    )
    affected_data: str = Field(description="What data is affected")
    priority: int = Field(
        ge=1, le=10, description="Priority 1-10 based on actual business impact"
    )
    is_expected: bool = Field(
        description="Whether this issue is expected given the domain context"
    )


class Recommendation(BaseModel):
    """An actionable recommendation."""

    action: str = Field(description="What should be done")
    reason: str = Field(description="Why this action is recommended")
    effort: str = Field(description="Estimated effort: low, medium, high")


class QualityInterpretation(BaseModel):
    """Interpreted quality results with business context."""

    overall_summary: str = Field(
        description="Executive summary of data quality in business terms"
    )
    overall_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Overall quality score 0-100 based on business impact",
    )
    critical_findings: list[Finding] = Field(
        description="Issues that require immediate attention"
    )
    warnings: list[Finding] = Field(
        description="Issues that should be investigated"
    )
    acceptable_issues: list[Finding] = Field(
        description="Issues that are acceptable given the context"
    )
    recommendations: list[Recommendation] = Field(
        description="Prioritized actionable recommendations"
    )
    context_notes: str = Field(
        description="Important context about why certain patterns exist"
    )


INTERPRETATION_PROMPT = """You are a data quality analyst who interprets results in business context.

Database Context:
Domain: {domain}
Purpose: {purpose}
Data characteristics: {characteristics}

Table: {table_name}

Quality Checks Run:
{checks_summary}

Results:
{results}

Sample Failures:
{failure_examples}

Your job: Interpret these results for a business audience.

1. What do the failures mean for THIS business/domain?
2. Which issues are critical vs acceptable?
3. Are any failures EXPECTED given the domain context? (e.g., historical data may have missing fields)
4. What should be done about each issue?
5. What is the overall health of this data?

Prioritize by business impact, not just failure count.
Provide context - explain WHY certain patterns exist in this domain.
Be actionable - give specific recommendations."""


class QualityInterpreterAgent:
    """Agent that interprets quality check results in business terms."""

    def __init__(self):
        """Initialize quality interpreter agent."""
        self.model = get_model()
        self.agent = Agent(
            self.model,
            output_type=QualityInterpretation,
            instructions=INTERPRETATION_PROMPT,
            retries=3,
        )

    async def interpret_results(
        self,
        table_name: str,
        db_context: DatabaseContext,
        checks: list[QualityCheck],
        results: list[dict],
        failure_examples: dict,
    ) -> QualityInterpretation:
        """Interpret quality check results.

        Args:
            table_name: Name of the table
            db_context: Database context
            checks: List of checks that were run
            results: List of {check_id, violations_count, passed} dicts
            failure_examples: Dict of check_id -> sample failing rows

        Returns:
            QualityInterpretation with business-aware analysis
        """
        # Format inputs
        checks_summary = self._format_checks(checks)
        results_text = self._format_results(checks, results)
        failures_text = self._format_failures(failure_examples)

        # Format the prompt with actual data
        prompt = INTERPRETATION_PROMPT.format(
            domain=db_context.domain,
            purpose=db_context.purpose,
            characteristics=db_context.data_characteristics,
            table_name=table_name,
            checks_summary=checks_summary,
            results=results_text,
            failure_examples=failures_text,
        )

        # Run agent
        result = await self.agent.run(prompt)

        return result.output

    def _format_checks(self, checks: list[QualityCheck]) -> str:
        """Format checks for prompt.

        Args:
            checks: List of QualityCheck objects

        Returns:
            Formatted string
        """
        formatted = []
        for check in checks:
            formatted.append(
                f"\n{check.check_id} ({check.severity}):\n"
                f"  Description: {check.description}\n"
                f"  Rationale: {check.rationale}\n"
                f"  Expected pass rate: {check.expected_pass_rate*100:.0f}%"
            )
        return "\n".join(formatted)

    def _format_results(
        self, checks: list[QualityCheck], results: list[dict]
    ) -> str:
        """Format results for prompt.

        Args:
            checks: List of checks
            results: List of result dicts

        Returns:
            Formatted string
        """
        # Create check lookup
        check_map = {c.check_id: c for c in checks}

        formatted = []
        for result in results:
            check_id = result.get("check_id")
            violations = result.get("violations_count", 0)
            passed = result.get("passed", True)

            check = check_map.get(check_id)
            if check:
                status = "✓ PASSED" if passed else "✗ FAILED"
                formatted.append(
                    f"{check_id}: {status} ({violations} violations)\n"
                    f"  Check: {check.description}"
                )

        return "\n".join(formatted)

    def _format_failures(self, failure_examples: dict) -> str:
        """Format failure examples for prompt.

        Args:
            failure_examples: Dict of check_id -> sample rows

        Returns:
            Formatted string
        """
        if not failure_examples:
            return "No failure examples available"

        formatted = []
        for check_id, examples in failure_examples.items():
            if examples:
                formatted.append(f"\n{check_id} failures:")
                for i, row in enumerate(examples[:3], 1):
                    # Show first 5 columns
                    sample = list(row.items())[:5]
                    row_str = ", ".join(f"{k}={v}" for k, v in sample)
                    formatted.append(f"  Example {i}: {row_str}")

        return "\n".join(formatted) if formatted else "No failure examples"
