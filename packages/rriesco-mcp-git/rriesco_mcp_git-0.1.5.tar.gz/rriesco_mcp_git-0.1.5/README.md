# Git MCP Server

Python MCP (Model Context Protocol) server for local git operations, providing native tool integration with Claude Code and other MCP clients.

## Features

- **6 Git Tools**: Commit, branch, push, pull, status, and sync operations
- **Native MCP Integration**: Works seamlessly with Claude Code
- **Conventional Commits**: Enforced commit message format with type prefixes
- **Branch Naming**: Enforced conventions (issue-N-description, feature-*, etc.)
- **Token Authentication**: Automatic GitHub token injection for remote operations

## Installation

### From PyPI

```bash
pip install git-mcp-server
# or with uv
uvx git-mcp-server
```

### From Source

```bash
git clone https://github.com/rriesco/git-mcp-server.git
cd git-mcp-server
uv sync
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | For push/pull | GitHub Personal Access Token for authenticated git operations |

### Claude Code Configuration

Add to your MCP configuration (`~/.config/claude-code/mcp-config.json`):

```json
{
  "mcpServers": {
    "git-manager": {
      "type": "stdio",
      "command": "uvx",
      "args": ["git-mcp-server"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `git_create_branch` | Create and checkout a new branch with naming conventions |
| `git_commit` | Create conventional commit with Claude attribution |
| `git_push` | Push commits to remote with upstream tracking |
| `git_pull` | Pull commits from remote |
| `git_status` | Get current branch, tracking info, and file changes |
| `git_sync_with_main` | Sync current branch with main (merge or rebase) |

## Usage Examples

### Create a Branch

```python
result = git_create_branch(
    issue_number=42,
    description="add-feature-x"
)
# Creates: issue-42-add-feature-x
```

### Commit Changes

```python
result = git_commit(
    type="feat",
    message="implement user authentication"
)
# Creates: feat: implement user authentication
#
# Co-Authored-By: Claude <noreply@anthropic.com>
```

### Check Status

```python
result = git_status()
# Returns: {branch, tracking, ahead, behind, staged, modified, untracked, clean}
```

### Sync with Main

```python
result = git_sync_with_main(
    main_branch="main",
    strategy="merge"  # or "rebase"
)
```

## Commit Types

The `git_commit` tool enforces conventional commit types:

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, semicolons, etc.) |
| `refactor` | Code refactoring |
| `perf` | Performance improvement |
| `test` | Adding or fixing tests |
| `build` | Build system or dependencies |
| `ci` | CI/CD configuration |
| `chore` | Maintenance tasks |
| `revert` | Revert previous commit |

## Branch Naming

The `git_create_branch` tool enforces naming conventions:

- `issue-<N>-<description>` - For GitHub issues
- `feature-<description>` - For features without issues
- `fix-<description>` - For bug fixes
- `refactor-<description>` - For refactoring

## Development

### Prerequisites

- Python >= 3.10
- uv (recommended) or pip
- Git

### Setup

```bash
git clone https://github.com/rriesco/git-mcp-server.git
cd git-mcp-server
uv sync
```

### Running Tests

```bash
# Unit tests only (fast)
uv run pytest -m "not integration" -v

# Integration tests (creates real git repos in temp directories)
uv run pytest -m integration -v

# All tests with coverage
uv run pytest --cov=git_mcp_server --cov-report=term-missing
```

### Type Checking

```bash
uv run mypy src/git_mcp_server --strict
```

## Architecture

```
Claude Code / MCP Client
      |
      | MCP Protocol (stdio)
      v
┌─────────────────────────────┐
│  Python FastMCP Server      │
│  - Tool Registry            │
│  - GitPython Client         │
│  - Error Handling           │
│  - Type Validation          │
└─────────────┬───────────────┘
              |
              | GitPython
              v
        Local Git Repo
```

## Project Structure

```
git-mcp-server/
├── src/git_mcp_server/
│   ├── server.py              # Server entry point
│   ├── tools/
│   │   ├── branch.py          # Branch operations
│   │   ├── commit.py          # Commit operations
│   │   ├── remote.py          # Push/pull operations
│   │   ├── status.py          # Status queries
│   │   └── sync.py            # Sync with main
│   └── utils/
│       ├── git_client.py      # Singleton Repo instance
│       └── errors.py          # Structured error handling
└── tests/
    ├── test_*.py              # Unit tests
    └── integration/           # Integration tests
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Links

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [GitPython Documentation](https://gitpython.readthedocs.io/)
- [FastMCP Framework](https://github.com/anthropics/fastmcp)
