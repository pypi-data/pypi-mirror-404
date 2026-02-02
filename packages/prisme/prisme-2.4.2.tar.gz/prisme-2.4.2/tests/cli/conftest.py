"""CLI test fixtures and configuration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner(mix_stderr=False)


@pytest.fixture
def isolated_runner(cli_runner: CliRunner):
    """Create a CLI runner with isolated filesystem."""
    with cli_runner.isolated_filesystem() as fs:
        yield cli_runner, Path(fs)


@pytest.fixture
def valid_spec_content() -> str:
    """Return valid spec file content."""
    return '''"""Test specification."""
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.stack import StackSpec

stack = StackSpec(
    name="test-project",
    version="1.0.0",
    models=[
        ModelSpec(
            name="User",
            fields=[
                FieldSpec(name="name", type=FieldType.STRING, required=True),
                FieldSpec(name="email", type=FieldType.STRING, unique=True),
            ],
        ),
        ModelSpec(
            name="Post",
            fields=[
                FieldSpec(name="title", type=FieldType.STRING, required=True),
                FieldSpec(name="content", type=FieldType.TEXT),
            ],
        ),
    ],
)
'''


@pytest.fixture
def valid_spec_file(tmp_path: Path, valid_spec_content: str) -> Path:
    """Create a valid spec file for testing."""
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_file = spec_dir / "models.py"
    spec_file.write_text(valid_spec_content)
    return spec_file


@pytest.fixture
def invalid_spec_file(tmp_path: Path) -> Path:
    """Create an invalid spec file (syntax error)."""
    spec_file = tmp_path / "invalid_spec.py"
    spec_file.write_text("this is not valid python{{{")
    return spec_file


@pytest.fixture
def spec_missing_stack(tmp_path: Path) -> Path:
    """Create a spec file without a stack variable."""
    spec_file = tmp_path / "no_stack.py"
    spec_file.write_text("x = 1\ny = 2\n")
    return spec_file


@pytest.fixture
def mock_subprocess(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock subprocess.run for testing external commands."""
    mock = MagicMock()
    mock.return_value.returncode = 0
    mock.return_value.stdout = ""
    mock.return_value.stderr = ""
    monkeypatch.setattr("subprocess.run", mock)
    return mock


@pytest.fixture
def mock_popen(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock subprocess.Popen for testing background processes."""
    mock = MagicMock()
    mock.return_value.wait.return_value = 0
    mock.return_value.terminate.return_value = None
    monkeypatch.setattr("subprocess.Popen", mock)
    return mock
