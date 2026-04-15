# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cfut is a CLI wrapper for AWS CloudFormation, ECR, ECS, and DynamoDB operations. It simplifies verbose AWS CLI commands by using a `cfut.json` configuration file that maps template aliases to CloudFormation stacks.

## Commands

```bash
# Install dev dependencies
uv sync

# Type checking
uv run mypy cfut

# Format code
uv run ruff format cfut

# Run tests
uv run pytest tests/
```

Publishing is automated: create a GitHub release with tag `vX.Y.Z` and
`.github/workflows/publish.yml` builds and uploads to PyPI via trusted
publisher OIDC. Do not edit `version` in `pyproject.toml` manually — the
workflow rewrites it from the release tag.

## Architecture

```
cfut/
├── cli.py        # Main CLI, argument parsing, command handlers (do_* functions)
├── commands.py   # AWS interactions via subprocess calls to aws cli
├── models.py     # Dataclass models + JSON loader for cfut.json
└── dataclass_argparse.py  # CLI arg generation from dataclass models
```

**Entry point**: `cfut.cli:main` (installed as `cfut` command)

**Key flow**: User command → cli.py parses args → routes to handler → commands.py executes AWS CLI → polls status for create/update/delete operations

**Configuration**: `cfut.json` in working directory defines AWS profile, template aliases, ECR/ECS settings

## Key Constraints

- Config models are stdlib dataclasses; JSON load/dump via `load_inifile` / `dump_inifile` in `models.py`
- AWS operations use subprocess calls to `aws` CLI (not boto3)
- Stack operations poll until completion using status rules defined in commands.py
