# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cfut is a CLI wrapper for AWS CloudFormation, ECR, ECS, and DynamoDB operations. It simplifies verbose AWS CLI commands by using a `cfut.json` configuration file that maps template aliases to CloudFormation stacks.

## Commands

```bash
# Type checking
python tasks.py check

# Format code
python tasks.py format

# Run tests
python tasks.py test

# Publish to PyPI
python tasks.py publish
```

## Architecture

```
cfut/
├── cli.py        # Main CLI, argument parsing, command handlers (do_* functions)
├── commands.py   # AWS interactions via subprocess calls to aws cli
├── models.py     # Pydantic v1 models for cfut.json configuration
└── pydantic_argparse.py  # CLI arg generation from Pydantic models
```

**Entry point**: `cfut.cli:main` (installed as `cfut` command)

**Key flow**: User command → cli.py parses args → routes to handler → commands.py executes AWS CLI → polls status for create/update/delete operations

**Configuration**: `cfut.json` in working directory defines AWS profile, template aliases, ECR/ECS settings

## Key Constraints

- Uses Pydantic v1 (pinned to `<2`)
- AWS operations use subprocess calls to `aws` CLI (not boto3)
- Stack operations poll until completion using status rules defined in commands.py
