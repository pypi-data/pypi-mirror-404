# CLAUDE.md

> Project context for Claude Code sessions. See also: [AGENT.md](AGENT.md) | [CONTRIBUTING.md](CONTRIBUTING.md)

## Project

Prism (`prisme` on PyPI) is a code generation framework that produces full-stack CRUD applications from Pydantic model specifications. Python 3.13+, MIT licensed, v0.12.1.

Always use `uv run` to execute Python, pytest, and prisme commands (e.g., `uv run python`, `uv run pytest`, `uv run prisme`).

## Skills

- **[prism-cli](.claude/skills/prism-cli/SKILL.md)** — Prism CLI commands, spec model reference, and generated project structure
- **[generate-prism-spec](.claude/skills/generate-prism-spec/SKILL.md)** — Generate a StackSpec from a natural-language description (`/generate-prism-spec`)
- **[develop-prism](.claude/skills/develop-prism/SKILL.md)** — Develop features and fix bugs in the Prism framework itself
