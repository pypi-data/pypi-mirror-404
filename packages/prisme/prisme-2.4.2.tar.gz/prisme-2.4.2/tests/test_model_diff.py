"""Tests for prism.tracking.model_diff field change detection."""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorResult
from prisme.tracking.model_diff import (
    detect_field_changes,
    detect_model_changes,
)

OLD_MODEL = """\
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    legacy_status: Mapped[str] = mapped_column(String(50))
"""

NEW_MODEL = """\
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
"""


class TestDetectFieldChanges:
    def test_added_fields(self) -> None:
        changes = detect_field_changes(OLD_MODEL, NEW_MODEL)
        assert len(changes) == 1
        assert changes[0].model_name == "User"
        assert changes[0].added == ["password_reset_token"]
        assert changes[0].removed == ["legacy_status"]

    def test_no_changes(self) -> None:
        changes = detect_field_changes(OLD_MODEL, OLD_MODEL)
        assert changes == []

    def test_new_model_all_added(self) -> None:
        changes = detect_field_changes("", NEW_MODEL)
        assert len(changes) == 1
        assert changes[0].model_name == "User"
        assert sorted(changes[0].added) == ["email", "id", "name", "password_reset_token"]
        assert changes[0].removed == []

    def test_removed_fields_only(self) -> None:
        changes = detect_field_changes(NEW_MODEL, OLD_MODEL)
        assert len(changes) == 1
        assert changes[0].added == ["legacy_status"]
        assert changes[0].removed == ["password_reset_token"]

    def test_formatting_only_no_changes(self) -> None:
        """Whitespace or comment changes without field changes produce no results."""
        old = """\
class Item(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
"""
        new = """\
# Updated formatting
class Item(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
"""
        changes = detect_field_changes(old, new)
        assert changes == []

    def test_multiple_classes(self) -> None:
        old = """\
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)

class Order(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(50))
"""
        new = """\
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255))

class Order(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
"""
        changes = detect_field_changes(old, new)
        assert len(changes) == 2
        user_change = next(c for c in changes if c.model_name == "User")
        order_change = next(c for c in changes if c.model_name == "Order")
        assert user_change.added == ["email"]
        assert order_change.removed == ["status"]


class TestDetectModelChanges:
    def test_new_file(self, tmp_path: Path) -> None:
        """Non-existent file means all fields are added."""
        result = GeneratorResult(
            files=[
                GeneratedFile(
                    path=tmp_path / "models" / "user.py",
                    content=NEW_MODEL,
                )
            ],
            written=1,
        )
        changes = detect_model_changes(result)
        assert len(changes) == 1
        assert changes[0].model_name == "User"
        assert len(changes[0].added) == 4

    def test_changed_file(self, tmp_path: Path) -> None:
        model_file = tmp_path / "user.py"
        model_file.write_text(OLD_MODEL)

        result = GeneratorResult(
            files=[GeneratedFile(path=model_file, content=NEW_MODEL)],
            written=1,
        )
        changes = detect_model_changes(result)
        assert len(changes) == 1
        assert changes[0].added == ["password_reset_token"]
        assert changes[0].removed == ["legacy_status"]

    def test_unchanged_file(self, tmp_path: Path) -> None:
        model_file = tmp_path / "user.py"
        model_file.write_text(OLD_MODEL)

        result = GeneratorResult(
            files=[GeneratedFile(path=model_file, content=OLD_MODEL)],
            written=1,
        )
        changes = detect_model_changes(result)
        assert changes == []

    def test_non_model_file_skipped(self, tmp_path: Path) -> None:
        result = GeneratorResult(
            files=[
                GeneratedFile(
                    path=tmp_path / "router.py",
                    content="from fastapi import APIRouter\n",
                )
            ],
            written=1,
        )
        changes = detect_model_changes(result)
        assert changes == []
