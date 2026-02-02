"""Execute a saved generation plan."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from prisme.planning.planner import GenerationPlan, load_plan


class PlanExecutionError(Exception):
    """Raised when plan execution fails."""


def apply_plan(output_dir: Path) -> GenerationPlan:
    """Load and execute a saved generation plan.

    This re-runs generation but only for files included in the plan.
    The plan acts as a filter — only planned files are written.

    Args:
        output_dir: Project directory containing .prisme/plan.json.

    Returns:
        The plan that was executed.

    Raises:
        PlanExecutionError: If no plan exists or execution fails.
    """
    plan = load_plan(output_dir)
    if plan is None:
        raise PlanExecutionError("No plan found. Run 'prisme plan' first to create a plan.")

    return plan
