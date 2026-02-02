"""Generate a plan from dry-run results."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class PlannedFile:
    """A file that will be created, modified, or deleted."""

    path: str
    action: str  # "create", "modify", "skip"
    strategy: str  # "always_overwrite", "generate_once"
    content_hash: str | None = None
    diff_summary: str | None = None


@dataclass
class GenerationPlan:
    """A saved generation plan."""

    created_at: str = ""
    spec_path: str = ""
    project_path: str | None = None
    files: list[PlannedFile] = field(default_factory=list)

    @property
    def creates(self) -> list[PlannedFile]:
        return [f for f in self.files if f.action == "create"]

    @property
    def modifies(self) -> list[PlannedFile]:
        return [f for f in self.files if f.action == "modify"]

    @property
    def skips(self) -> list[PlannedFile]:
        return [f for f in self.files if f.action == "skip"]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GenerationPlan:
        files = [PlannedFile(**f) for f in data.get("files", [])]
        return cls(
            created_at=data.get("created_at", ""),
            spec_path=data.get("spec_path", ""),
            project_path=data.get("project_path"),
            files=files,
        )


PLAN_FILE = ".prisme/plan.json"


def create_plan(
    output_dir: Path,
    generated_files: list[Any],
    spec_path: str = "",
    project_path: str | None = None,
) -> GenerationPlan:
    """Create a generation plan from dry-run results.

    Args:
        output_dir: The project output directory.
        generated_files: List of GeneratedFile objects from a dry-run.
        spec_path: Path to the spec file used.
        project_path: Path to the project spec file used.

    Returns:
        The generated plan.
    """
    from prisme.tracking.manifest import hash_content

    plan = GenerationPlan(
        created_at=datetime.now().isoformat(),
        spec_path=spec_path,
        project_path=project_path,
    )

    for gf in generated_files:
        full_path = output_dir / gf.path
        if full_path.exists():
            action = "modify" if gf.strategy.value == "always_overwrite" else "skip"
        else:
            action = "create"

        plan.files.append(
            PlannedFile(
                path=str(gf.path),
                action=action,
                strategy=gf.strategy.value,
                content_hash=hash_content(gf.content),
            )
        )

    return plan


def save_plan(plan: GenerationPlan, output_dir: Path) -> Path:
    """Save a plan to .prisme/plan.json.

    Args:
        plan: The plan to save.
        output_dir: Project directory.

    Returns:
        Path to the saved plan file.
    """
    plan_path = output_dir / PLAN_FILE
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan.to_dict(), indent=2) + "\n")
    return plan_path


def load_plan(output_dir: Path) -> GenerationPlan | None:
    """Load a saved plan from .prisme/plan.json.

    Args:
        output_dir: Project directory.

    Returns:
        The loaded plan, or None if no plan exists.
    """
    plan_path = output_dir / PLAN_FILE
    if not plan_path.exists():
        return None

    data = json.loads(plan_path.read_text())
    return GenerationPlan.from_dict(data)
