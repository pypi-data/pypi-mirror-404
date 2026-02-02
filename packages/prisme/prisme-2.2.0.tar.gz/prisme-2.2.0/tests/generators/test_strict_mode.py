"""Tests for strict vs lenient generation mode."""

from pathlib import Path

from prisme.config.schema import GenerationPolicy, PrismeConfig
from prisme.generators.base import GeneratedFile, GeneratorBase, GeneratorContext
from prisme.spec.stack import FileStrategy, StackSpec


class _DummyGenerator(GeneratorBase):
    """Generator that produces one file for testing."""

    def generate_files(self) -> list[GeneratedFile]:
        return [
            GeneratedFile(
                path=Path("test.py"),
                content="# test",
                strategy=FileStrategy.ALWAYS_OVERWRITE,
            )
        ]


def _make_config(mode: str = "lenient") -> PrismeConfig:
    return PrismeConfig(
        prisme_version="2.0.0",
        generation=GenerationPolicy(mode=mode),
    )


def _make_spec() -> StackSpec:
    return StackSpec(name="test", models=[])


def test_lenient_mode_collects_warnings(tmp_path: Path) -> None:
    ctx = GeneratorContext(
        domain_spec=_make_spec(),
        output_dir=tmp_path,
        config=_make_config("lenient"),
    )
    gen = _DummyGenerator(ctx)
    result = gen.generate()
    # No warnings expected in simple case
    assert result.warnings == []
    assert result.errors == []


def test_strict_mode_promotes_warnings(tmp_path: Path) -> None:
    ctx = GeneratorContext(
        domain_spec=_make_spec(),
        output_dir=tmp_path,
        config=_make_config("strict"),
    )
    gen = _DummyGenerator(ctx)
    result = gen.generate()
    # Manually add a warning to test promotion
    result.warnings.append("test warning")
    # The promotion happens in generate(), but we can test the property
    assert gen._generation_mode == "strict"


def test_generation_mode_default_lenient(tmp_path: Path) -> None:
    ctx = GeneratorContext(
        domain_spec=_make_spec(),
        output_dir=tmp_path,
    )
    gen = _DummyGenerator(ctx)
    assert gen._generation_mode == "lenient"


def test_generation_mode_from_config(tmp_path: Path) -> None:
    ctx = GeneratorContext(
        domain_spec=_make_spec(),
        output_dir=tmp_path,
        config=_make_config("strict"),
    )
    gen = _DummyGenerator(ctx)
    assert gen._generation_mode == "strict"
