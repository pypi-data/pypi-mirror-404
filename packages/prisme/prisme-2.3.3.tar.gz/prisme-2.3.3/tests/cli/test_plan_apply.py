"""Tests for plan/apply workflow."""

from pathlib import Path

from prisme.planning.planner import (
    GenerationPlan,
    PlannedFile,
    load_plan,
    save_plan,
)


def test_plan_roundtrip(tmp_path: Path) -> None:
    plan = GenerationPlan(
        created_at="2025-01-01T00:00:00",
        spec_path="specs/models.py",
        files=[
            PlannedFile(path="src/main.py", action="create", strategy="always_overwrite"),
            PlannedFile(path="src/hooks.py", action="skip", strategy="generate_once"),
        ],
    )

    path = save_plan(plan, tmp_path)
    assert path.exists()

    loaded = load_plan(tmp_path)
    assert loaded is not None
    assert len(loaded.files) == 2
    assert len(loaded.creates) == 1
    assert len(loaded.skips) == 1


def test_load_plan_missing(tmp_path: Path) -> None:
    assert load_plan(tmp_path) is None


def test_plan_properties() -> None:
    plan = GenerationPlan(
        files=[
            PlannedFile(path="a", action="create", strategy="always_overwrite"),
            PlannedFile(path="b", action="modify", strategy="always_overwrite"),
            PlannedFile(path="c", action="skip", strategy="generate_once"),
        ],
    )
    assert len(plan.creates) == 1
    assert len(plan.modifies) == 1
    assert len(plan.skips) == 1


def test_plan_from_dict() -> None:
    data = {
        "created_at": "2025-01-01",
        "spec_path": "spec.py",
        "files": [
            {"path": "a.py", "action": "create", "strategy": "always_overwrite"},
        ],
    }
    plan = GenerationPlan.from_dict(data)
    assert plan.spec_path == "spec.py"
    assert len(plan.files) == 1
