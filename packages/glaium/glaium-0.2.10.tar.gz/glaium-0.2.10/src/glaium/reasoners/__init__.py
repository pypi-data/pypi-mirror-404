"""
Glaium Reasoners - Reasoning engines for agent decision-making.

Provides:
- AnalyticalReasoner: Uses formulas, statistics, and ML models (no LLM)

LLM reasoning is handled server-side by the Optimizer. Agents use
`client.reason_async()` to submit data and receive structured
recommendations — no local LLM calls.

Example:
    ```python
    from glaium import Agent, CycleContext
    from glaium.reasoners import AnalyticalReasoner

    # Analytical reasoner (formula-based, runs locally)
    analytical = AnalyticalReasoner(organization_id="org-123")

    @agent.on_cycle
    def on_cycle(ctx: CycleContext) -> dict:
        inputs = fetch_data()

        # LLM reasoning: use SDK client (server-side)
        result = await client.reason_async(data_context=inputs)

        # Analytical reasoning: runs locally
        result = analytical.analyze(optimization=ctx.optimization, inputs=inputs)

        return {
            "inputs": inputs,
            "outputs": result.predicted_outputs,
        }
    ```
"""

from glaium.reasoners.analytical import AnalyticalReasoner
from glaium.reasoners.base import BaseReasoner, Reasoner
from glaium.reasoners.models import (
    Analysis,
    Anomaly,
    Breach,
    MetricFormula,
    OrganizationModel,
    Recommendation,
    ReasonerOutput,
    SolverResult,
    Trend,
)

__all__ = [
    # Reasoners
    "Reasoner",
    "BaseReasoner",
    "AnalyticalReasoner",
    # Output models
    "ReasonerOutput",
    "Analysis",
    "Anomaly",
    "Trend",
    "Breach",
    "Recommendation",
    "SolverResult",
    # Configuration models
    "MetricFormula",
    "OrganizationModel",
]
