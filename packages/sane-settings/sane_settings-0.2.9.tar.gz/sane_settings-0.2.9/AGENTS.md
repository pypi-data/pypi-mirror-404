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

## Release Workflow

**CRITICAL: PyPI publishing requires tag push**

The GitHub Actions workflow at `.github/workflows/build.yaml` triggers on tag pushes (`v*`), not regular commits:

```yaml
on:
  push:
    tags:
      - 'v*'  # Only triggers on tags like v0.2.8
```

**Proper release flow:**
1. Complete your feature/bug fix on a branch
2. Create PR and merge to main
3. On main: `just bump-patch` (creates commit + tag locally)
4. **CRITICAL**: Use `just push-all` to push BOTH commits AND tags
   - Wrong: `git push` (only pushes commits, tag stays local)
   - Right: `just push-all` (pushes commits + tags, triggers PyPI)
5. Verify tag exists on remote: `git ls-remote --tags origin`

**If you already pushed commits but not the tag:**
```bash
git push origin v0.2.8  # Push just the tag to trigger workflow
```

**Common pitfall:** Pushing a feature branch with `git push origin fix/branch` only pushes commits. The version tag created by `just bump-patch` remains local, so the PyPI workflow never triggers.

## Commits & Communication

- Be concise and direct
- If uncertain about requirements, ask clarifying questions
- For type-related bugs, check both `typing.Union` and `types.UnionType` handling
- Use available skills for git operations, testing, and PR creation
