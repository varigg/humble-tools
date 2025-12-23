# Python Development Philosophy & Guidelines

## Core Principles

### Simplicity Over Complexity

- Keep things as simple as possible
- Avoid premature decomposition and over-engineering
- Self-contained projects with all necessary infrastructure included
- Monorepo structure for most projects (unless multiple teams or significant scale requires separation)

### Pragmatic Production-Ready Development

"Production-ready" means deployable to the cloud as-is, without major infrastructure changes.

### Minimize Cognitive Load

- Centralized code in one location (search-friendly, easier to maintain)
- Short project names (ideally < 10 characters)
- No `snake_case` for project names; hyphens are acceptable
- Compile, test, containerize, and deploy from a single location

## Project Structure

### Standard Layout

```
project/
├── .github/              # CI/CD workflows, Dependabot config
├── .vscode/              # VSCode debugging and settings
├── docs/                 # Documentation (MkDocs static site)
├── project-api/          # Backend API
│   ├── data/
│   ├── notebooks/        # Jupyter for experimentation
│   ├── tools/            # Utility scripts
│   ├── src/
│   │   ├── app/          # Main application code
│   │   └── tests/        # Unit tests
│   ├── .python-version
│   ├── Dockerfile
│   ├── Makefile
│   ├── pyproject.toml
│   └── uv.lock
├── project-ui/           # Frontend (optional, project-dependent)
├── .gitignore
├── .pre-commit-config.yaml
├── docker-compose.yml
├── Makefile
└── README.md
```

### Architecture Decisions

- **API vs. Frontend split**: Depends on the project requirements
  - Keep browser apps light; delegate heavy processing to backend
  - No heavy data processing in UI layer
  - HTTP requests to backend for business logic
- Use `__init__.py` files to indicate Python modules

## Python Toolchain

### Essential Tools

#### 1. uv (Package Manager & Build Tool)

- Primary tool for dependency management
- Commands: `uv init`, `uv add`, `uv sync`, `uv venv`
- `pyproject.toml` is the central configuration file

#### 2. ruff (Linter & Formatter)

- Super-fast combined linter and formatter
- Replaces: isort, flake8, autoflake
- Supports PEP 8 out of the box
- Commands: `ruff check`, `ruff format`

#### 3. ty (Type Checker)

- Modern type checker for Python
- Pair with `typing` module for static typing
- Type annotations improve code quality and catch errors early
- Don't worry about writing more code if it improves quality

#### 4. pytest (Testing)

- Standard testing framework
- Simple test files: `test_<unit_or_module>.py`
- Run with: `uv run pytest`
- Supports fixtures, parameterization, rich plugin ecosystem

#### 5. Pydantic (Data Validation & Settings)

- Data validation and settings management
- Use Pydantic Settings for configuration (API keys, database URLs, etc.)
- Automatic loading from environment variables or `.env` files
- Never hardcode configuration values

### Web Frameworks

#### FastAPI

- Primary choice for building APIs
- Automatic validation, serialization, and documentation
- Built on Starlette and Pydantic
- Excellent performance and type safety

#### Flask

- Alternative web framework (project-dependent)
- Use when FastAPI's features aren't needed
- Good for simpler web applications

### Language Features

#### Dataclasses

- Use for data containers
- Reduces boilerplate (`__init__`, `__repr__`, `__eq__`)
- Clean, readable syntax

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
```

## Version Control & CI/CD

### GitHub Actions

- Primary CI/CD tool
- Support for multiple OSs (ubuntu-latest, windows-latest, macos-latest)
- Use Docker in workflows for isolated environments

### Dependabot

- Automatic dependency updates
- Weekly schedule recommended
- Configure in `.github/dependabot.yml`

### Gitleaks

- Prevent committing sensitive information
- Run via pre-commit hooks
- No excuse not to use it

### Pre-commit Hooks

- Run checks before committing
- Include: ruff (linter + formatter), gitleaks
- Configuration in `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.3
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.27.2
    hooks:
      - id: gitleaks
```

## Infrastructure Management

### Make

- Automate common tasks with Makefiles
- Create shortcuts for: testing, linting, building, running
- Use at both project root and subdirectory levels

```makefile
test:
	uv run pytest

format-fix:
	uv run ruff format $(DIR)
	uv run ruff check --select I --fix
```

### Docker & Docker Compose

- Package applications with dependencies into containers
- Use Docker Compose to connect services locally
- Ensures parity with production environments
- Run entire stack with: `docker compose up --build -d`

Example `Dockerfile` pattern:

```dockerfile
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY uv.lock pyproject.toml README.md ./
RUN uv sync --frozen --no-cache

COPY src/app app/
COPY tools tools/

CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "8000", "--host", "0.0.0.0"]
```

## Documentation

### MkDocs

- Static site generation for project documentation
- Host on GitHub Pages
- Copy aesthetically pleasing designs from similar projects
- Simple CSS modifications (fonts, colors)
- **Every GitHub project should have its own website**

## Best Practices

1. **Avoid premature optimization** - Don't split into multiple repos until truly necessary
2. **Type everything** - Use type hints consistently for better error detection
3. **Test thoroughly** - Write tests as you develop
4. **Validate inputs** - Use Pydantic for all external data
5. **Keep it DRY** - Use Makefiles and automation to avoid repetitive tasks
6. **Security first** - Always use Gitleaks and environment variables for secrets
7. **Document everything** - README, docs site, inline comments where needed
8. **Containerize** - Docker for development and production parity
9. **Automate CI/CD** - GitHub Actions for every project
10. **Short and sweet** - Favor brevity in naming, structure, and code

## Philosophy Summary

> "I prefer to keep things as simple as possible, compile, test, containerize, and deploy from a single location."

- Choose Python for AI/ML work (it's the ecosystem standard)
- Embrace modern Python tooling (uv, ruff, ty)
- Value type safety and data validation
- Keep projects self-contained and deployable
- Automate everything that can be automated
- Avoid over-engineering and premature splitting
- Make the code clean, tested, and production-ready from day one
