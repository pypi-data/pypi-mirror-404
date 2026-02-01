# llmtokens - Developer Guide

## Package Structure

```
llmtokens/
├── .gitignore
├── CLAUDE.md              # This file
├── LICENSE                # MIT license
├── README.md              # User-facing documentation
├── pyproject.toml         # Build configuration
└── src/
    └── llmtokens/
        ├── __init__.py    # Package marker
        └── cli.py         # Main CLI logic
```

## Build System

This package uses:
- **src layout**: Package code lives in `src/llmtokens/` to ensure clean imports during development
- **hatchling**: Modern, minimal build backend that works well with uv/uvx
- **Python 3.12+**: Requires modern Python for type hints and language features

## Development Commands

### Install in development mode
```bash
uv pip install -e .
```

### Run locally
```bash
uv run llmtokens --help
echo "hello world" | uv run llmtokens
```

### Run tests
```bash
uv run --extra dev pytest
# Or with verbose output
uv run --extra dev pytest -v
```

### Build package
```bash
uv build
```

### Lint (when configured)
```bash
uv run ruff check .
uv run mypy src/
```

## Dependencies

Runtime dependencies (installed automatically):
- `huggingface_hub` - Download tokenizers from HuggingFace Hub
- `tokenizers` - Fast tokenization
- `jinja2` - Chat template rendering
- `tiktoken` - OpenAI tokenizers

Development dependencies (optional):
- `pytest` - Testing framework

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`

**Examples:**
```
feat: add support for custom chat templates
fix: handle missing tokenizer_config.json gracefully
docs: update README with gated model instructions
refactor: extract template rendering to separate function
chore: update dependencies
test: add tests for message parsing
```

Use lowercase bullet points for multiple changes in commit body.

Do not add Claude attribution unless Claude has helped write changes in the commit.

## Testing

The project includes basic smoke tests using pytest:

**Test categories:**
- Tokenizer loading (tiktoken and HuggingFace)
- Token counting
- Message parsing (JSON vs auto-wrap)
- Chat template rendering
- CLI end-to-end tests

**Running tests:**
```bash
uv run --extra dev pytest -v
```

**Test approach:**
- Import and call functions directly (not subprocess)
- Use pytest fixtures (monkeypatch, capsys)
- Real tokenizers (cached by HF/tiktoken, fast enough)
- No mocking for basic tests

## Key Conventions

- **Entry point**: CLI is exposed via `pyproject.toml` scripts section
  - Command: `llmtokens`
  - Target: `llmtokens.cli:main`

- **Version**: Defined in `pyproject.toml` (modern PEP 621 approach)

## Publishing (future)

When ready to publish to PyPI:
```bash
# Build
uv build

# Publish (requires PyPI credentials)
uv publish
```

## Testing the Package

Before publishing, verify the package works correctly:
```bash
# Test help
uv run llmtokens --help

# Test basic functionality
echo "hello world" | uv run llmtokens

# Test with file input
echo "test content" > /tmp/test.txt
uv run llmtokens /tmp/test.txt

# Test multiple models
echo "compare models" | uv run llmtokens -m Qwen/Qwen2.5-0.5B -m meta-llama/Llama-3.3-70B-Instruct
```
