# Agent Instructions

Guidelines for AI agents working on this codebase. See also `CLAUDE.md` for
project-specific architectural notes.

## Code Quality

Use ruff for formatting and linting:
```bash
uv run ruff format .
uv run ruff check . --fix
```

Run both before committing changes.

## Package Management

Use uv, not pip:
```bash
uv add <package>    # Add dependency
uv sync             # Install dependencies (incl. dev group)
uv run <command>    # Run in venv
```

## Testing

```bash
uv run pytest tests/
```

## Releasing

Versions are managed by the GitHub Actions publish workflow. Do NOT edit
`version` in `pyproject.toml` manually — it is rewritten from the release tag
at build time. Cut a release with:

```bash
gh release create v1.8.6 --notes "..."
```
