# Project: sane-settings

A Python library for environment variable-based configuration management with explicit, type-safe settings loading and clear error messages.

Built with: Python 3.10+, uv (package manager), just (task runner), loguru, pytest

## North Star Preferences

- Explicit is better than implicit - always fail fast with clear error messages for missing env vars
- Support both `Optional[T]` and `T | None` syntax for optional fields
- Keep type annotations accurate - use `Any` for function parameters that accept multiple types
- Log debug messages when defaults are used to help catch typos in env vars
- Never expose secrets in logs (use `SecretStr` wrapper)

## Documentation & Resources

- Project docs: See `README.md` for usage examples and API reference
- Requirements: Track features in your issue tracker or project board
- Architecture notes: See existing `CLAUDE.md` for detailed component breakdown

## Workflow Commands

- List commands: `just`
- Run tests: `uv run pytest -v`
- Install deps: `uv sync`
- Bump version: `just bump-patch|minor|major`
- Push release: `just push-all`
- Show version: `just version`

Always run tests before committing: `uv run pytest -v`

## Git Workflow

- Work on feature branches: `git checkout -b feat/description` or `fix/description`
- Use conventional commits: `feat:`, `fix:`, `refactor:`, etc.
- Keep branches focused on single changes
- Run `just bump-patch` (or minor/major) to version and tag releases
- Use `just push-all` to push commits and tags together
- Main branch is protected—never push directly to main

## Commits & Communication

- Be concise and direct
- If uncertain about requirements, ask clarifying questions
- For type-related bugs, check both `typing.Union` and `types.UnionType` handling
- Use available skills for git operations, testing, and PR creation
