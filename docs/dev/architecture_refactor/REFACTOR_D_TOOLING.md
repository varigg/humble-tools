# Refactor Phase D: Tooling & Quality

**Estimated Duration:** Ongoing  
**Difficulty:** Low to Medium  
**Impact:** High (long-term code quality and maintainability)

---

## Overview

This phase focuses on establishing robust tooling, automation, and continuous quality improvements. These are ongoing tasks that improve the development workflow and ensure code quality over time.

---

## Task D.1: Set Up Dependabot

**Priority:** High  
**Estimated Time:** 30 minutes  
**Files to Create:**

- [.github/dependabot.yml](../../../.github/dependabot.yml)

### Tasks

- [ ] **D.1.1** Create `.github/dependabot.yml` configuration

  ```yaml
  version: 2
  updates:
    # Python dependencies
    - package-ecosystem: "pip"
      directory: "/"
      schedule:
        interval: "weekly"
        day: "monday"
        time: "09:00"
      open-pull-requests-limit: 10
      reviewers:
        - "varigg" # Replace with actual GitHub username
      assignees:
        - "varigg"
      commit-message:
        prefix: "deps"
        prefix-development: "deps-dev"
        include: "scope"
      labels:
        - "dependencies"
        - "python"
      # Group minor and patch updates together
      groups:
        minor-and-patch:
          patterns:
            - "*"
          update-types:
            - "minor"
            - "patch"

    # GitHub Actions
    - package-ecosystem: "github-actions"
      directory: "/"
      schedule:
        interval: "weekly"
        day: "monday"
        time: "09:00"
      labels:
        - "dependencies"
        - "github-actions"
  ```

- [ ] **D.1.2** Enable Dependabot in GitHub repository settings

  - Go to repository Settings → Security → Code security and analysis
  - Enable "Dependabot alerts"
  - Enable "Dependabot security updates"

- [ ] **D.1.3** Configure auto-merge for Dependabot PRs (optional)

  - Only for patch updates with passing tests
  - Requires GitHub Actions workflow

- [ ] **D.1.4** Document Dependabot workflow in README or docs

  ```markdown
  ## Dependency Management

  This project uses Dependabot for automated dependency updates:

  - Weekly checks every Monday at 9 AM
  - Creates PRs for outdated dependencies
  - Groups minor and patch updates together
  - Separate PRs for major version updates (review carefully)

  ### Reviewing Dependabot PRs

  1. Check that all tests pass
  2. Review changelog if major version
  3. Merge if tests pass and no breaking changes
  ```

### Validation

- Wait for first Dependabot PR to be created
- Review and merge a Dependabot PR to verify workflow

---

## Task D.2: Add GitHub Actions for CI/CD

**Priority:** High  
**Estimated Time:** 2-3 hours  
**Files to Create:**

- [.github/workflows/ci.yml](../../../.github/workflows/ci.yml)
- [.github/workflows/release.yml](../../../.github/workflows/release.yml) (optional)

### Tasks

- [ ] **D.2.1** Create main CI workflow `.github/workflows/ci.yml`

  ```yaml
  name: CI

  on:
    push:
      branches: [main, develop]
    pull_request:
      branches: [main]

  jobs:
    test:
      runs-on: ${{ matrix.os }}
      strategy:
        fail-fast: false
        matrix:
          os: [ubuntu-latest, macos-latest, windows-latest]
          python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]

      steps:
        - uses: actions/checkout@v4

        - name: Install uv
          uses: astral-sh/setup-uv@v2
          with:
            version: "latest"

        - name: Set up Python ${{ matrix.python-version }}
          uses: actions/setup-python@v5
          with:
            python-version: ${{ matrix.python-version }}

        - name: Install dependencies
          run: |
            uv sync --all-extras --dev

        - name: Run tests
          run: |
            uv run pytest --cov=humble_tools --cov-report=xml --cov-report=term

        - name: Upload coverage to Codecov
          uses: codecov/codecov-action@v4
          with:
            file: ./coverage.xml
            fail_ci_if_error: false

    lint:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4

        - name: Install uv
          uses: astral-sh/setup-uv@v2

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: "3.11"

        - name: Install dependencies
          run: uv sync --dev

        - name: Run ruff check
          run: uv run ruff check src/ tests/

        - name: Run ruff format check
          run: uv run ruff format --check src/ tests/

    type-check:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4

        - name: Install uv
          uses: astral-sh/setup-uv@v2

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: "3.11"

        - name: Install dependencies
          run: uv sync --dev

        - name: Run ty
          run: uv run ty src/humble_tools
  ```

- [ ] **D.2.2** Create release workflow `.github/workflows/release.yml` (optional)

  ```yaml
  name: Release

  on:
    push:
      tags:
        - "v*.*.*"

  jobs:
    release:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4

        - name: Install uv
          uses: astral-sh/setup-uv@v2

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: "3.11"

        - name: Build package
          run: uv build

        - name: Create GitHub Release
          uses: softprops/action-gh-release@v1
          with:
            files: dist/*
            generate_release_notes: true
          env:
            GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  ```

- [ ] **D.2.3** Add status badges to README

  ```markdown
  # Humble Tools

  [![CI](https://github.com/varigg/humblebundle/workflows/CI/badge.svg)](https://github.com/varigg/humblebundle/actions/workflows/ci.yml)
  [![codecov](https://codecov.io/gh/varigg/humblebundle/branch/main/graph/badge.svg)](https://codecov.io/gh/varigg/humblebundle)
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
  ```

- [ ] **D.2.4** Configure branch protection rules
  - Require status checks to pass before merging
  - Require branches to be up to date
  - Require review from code owners

### Validation

- Push a commit and verify CI runs
- Create a PR and verify all checks pass
- Check that badges display correctly in README

---

## Task D.3: Add Code Coverage Reporting

**Priority:** Medium  
**Estimated Time:** 1 hour  
**Files to Modify:**

- [pyproject.toml](../../../pyproject.toml)
- [.github/workflows/ci.yml](../../../.github/workflows/ci.yml) (already done in D.2)

### Tasks

- [ ] **D.3.1** Configure pytest-cov in `pyproject.toml`

  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  asyncio_default_fixture_loop_scope = "function"
  testpaths = ["tests"]
  python_files = ["test_*.py"]
  python_classes = ["Test*"]
  python_functions = ["test_*"]

  # Coverage configuration
  addopts = [
      "--cov=humble_tools",
      "--cov-report=term-missing",
      "--cov-report=html",
      "--cov-report=xml",
  ]

  [tool.coverage.run]
  source = ["src/humble_tools"]
  omit = [
      "*/tests/*",
      "*/__pycache__/*",
      "*/.venv/*",
  ]

  [tool.coverage.report]
  exclude_lines = [
      "pragma: no cover",
      "def __repr__",
      "raise AssertionError",
      "raise NotImplementedError",
      "if __name__ == .__main__.:",
      "if TYPE_CHECKING:",
      "@abstractmethod",
  ]
  precision = 2
  ```

- [ ] **D.3.2** Sign up for Codecov account

  - Visit https://codecov.io
  - Connect GitHub repository
  - Add `CODECOV_TOKEN` to GitHub secrets if needed

- [ ] **D.3.3** Set coverage targets

  ```toml
  [tool.coverage.report]
  # ... existing config ...
  fail_under = 80  # Fail if coverage below 80%
  ```

- [ ] **D.3.4** Add coverage report to gitignore

  ```gitignore
  # Coverage
  .coverage
  htmlcov/
  coverage.xml
  ```

- [ ] **D.3.5** Document coverage in README

  ````markdown
  ## Development

  ### Running Tests with Coverage

  ```bash
  uv run pytest --cov
  ```
  ````

  To see detailed HTML report:

  ```bash
  uv run pytest --cov --cov-report=html
  open htmlcov/index.html
  ```

  ```

  ```

### Validation

```bash
uv run pytest --cov
# Should see coverage report
open htmlcov/index.html
# Should see detailed HTML report
```

---

## Task D.4: Add Code Complexity Metrics with Radon

**Priority:** Low  
**Estimated Time:** 1 hour  
**Files to Create:**

- [.github/workflows/metrics.yml](../../../.github/workflows/metrics.yml) (optional)

### Tasks

- [ ] **D.4.1** Install radon

  ```bash
  uv add --dev radon
  ```

- [ ] **D.4.2** Add radon checks to Makefile

  ```makefile
  .PHONY: complexity
  complexity:
  	@echo "Checking code complexity..."
  	uv run radon cc src/humble_tools -a -nc

  .PHONY: maintainability
  maintainability:
  	@echo "Checking maintainability index..."
  	uv run radon mi src/humble_tools -n B

  .PHONY: metrics
  metrics: complexity maintainability
  	@echo "All metrics checked"
  ```

- [ ] **D.4.3** Set complexity thresholds

  ```bash
  # A = 1-5 (simple)
  # B = 6-10 (somewhat complex)
  # C = 11-20 (complex)
  # D = 21-50 (very complex)
  # E = 51+ (extremely complex)
  # F = 100+ (unmaintainable)

  # Fail on anything rated D or worse
  uv run radon cc src/humble_tools --min D --max F
  ```

- [ ] **D.4.4** Add complexity check to pre-commit (optional)

  ```yaml
  # In .pre-commit-config.yaml
  - repo: local
    hooks:
      - id: radon-complexity
        name: Check code complexity
        entry: uv run radon cc src/humble_tools --min D
        language: system
        always_run: true
        pass_filenames: false
  ```

- [ ] **D.4.5** Create metrics workflow for tracking over time

  ```yaml
  # .github/workflows/metrics.yml
  name: Code Metrics

  on:
    push:
      branches: [main]
    schedule:
      - cron: "0 0 * * 0" # Weekly on Sunday

  jobs:
    metrics:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4

        - name: Install uv
          uses: astral-sh/setup-uv@v2

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: "3.11"

        - name: Install dependencies
          run: uv sync --dev

        - name: Run complexity analysis
          run: |
            uv run radon cc src/humble_tools -a -s --json > complexity.json

        - name: Run maintainability analysis
          run: |
            uv run radon mi src/humble_tools --json > maintainability.json

        - name: Upload metrics
          uses: actions/upload-artifact@v4
          with:
            name: code-metrics
            path: |
              complexity.json
              maintainability.json
  ```

- [ ] **D.4.6** Document acceptable complexity levels

  ````markdown
  ## Code Quality Standards

  ### Complexity Thresholds

  - Functions should have cyclomatic complexity ≤ 10 (rating A-B)
  - Functions with complexity 11-20 (rating C) should be refactored when possible
  - Functions with complexity > 20 (rating D+) require justification or refactoring

  Check complexity:

  ```bash
  make complexity
  ```
  ````

  ```

  ```

### Validation

```bash
uv run radon cc src/humble_tools -a
uv run radon mi src/humble_tools
# Review output for any concerning metrics
```

---

## Task D.5: Set Up Documentation Site with MkDocs

**Priority:** Low  
**Estimated Time:** 3-4 hours  
**Files to Create:**

- [mkdocs.yml](../../../mkdocs.yml)
- [docs/index.md](../../../docs/index.md)
- [docs/installation.md](../../../docs/installation.md)
- [docs/usage.md](../../../docs/usage.md)
- [docs/development.md](../../../docs/development.md)
- [.github/workflows/docs.yml](../../../.github/workflows/docs.yml)

### Tasks

- [ ] **D.5.1** Install MkDocs and theme

  ```bash
  uv add --dev mkdocs mkdocs-material mkdocstrings[python]
  ```

- [ ] **D.5.2** Create `mkdocs.yml` configuration

  ```yaml
  site_name: Humble Tools
  site_description: CLI and TUI tools for managing Humble Bundle downloads
  site_author: Your Name
  repo_url: https://github.com/varigg/humblebundle
  repo_name: varigg/humblebundle

  theme:
    name: material
    palette:
      - scheme: default
        primary: indigo
        accent: indigo
        toggle:
          icon: material/brightness-7
          name: Switch to dark mode
      - scheme: slate
        primary: indigo
        accent: indigo
        toggle:
          icon: material/brightness-4
          name: Switch to light mode
    features:
      - navigation.tabs
      - navigation.sections
      - navigation.expand
      - search.suggest
      - search.highlight
      - content.code.copy

  nav:
    - Home: index.md
    - Installation: installation.md
    - Usage:
        - Getting Started: usage.md
        - TUI Guide: usage/tui.md
        - CLI Guide: usage/cli.md
    - Development:
        - Setup: development.md
        - Architecture: development/architecture.md
        - Contributing: development/contributing.md
    - API Reference: api/

  plugins:
    - search
    - mkdocstrings:
        handlers:
          python:
            options:
              docstring_style: google
              show_source: true

  markdown_extensions:
    - pymdownx.highlight
    - pymdownx.superfences
    - pymdownx.tabbed
    - pymdownx.details
    - admonition
    - toc:
        permalink: true
  ```

- [ ] **D.5.3** Create documentation pages

  - Move content from README.md to appropriate docs pages
  - Add API documentation using mkdocstrings
  - Add development guides
  - Add architecture documentation

- [ ] **D.5.4** Set up GitHub Pages deployment

  ```yaml
  # .github/workflows/docs.yml
  name: Documentation

  on:
    push:
      branches: [main]
    pull_request:
      branches: [main]

  jobs:
    deploy:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4

        - name: Install uv
          uses: astral-sh/setup-uv@v2

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: "3.11"

        - name: Install dependencies
          run: uv sync --dev

        - name: Build documentation
          run: uv run mkdocs build

        - name: Deploy to GitHub Pages
          if: github.event_name == 'push' && github.ref == 'refs/heads/main'
          uses: peaceiris/actions-gh-pages@v3
          with:
            github_token: ${{ secrets.GITHUB_TOKEN }}
            publish_dir: ./site
  ```

- [ ] **D.5.5** Add documentation link to README

  ```markdown
  ## Documentation

  Full documentation is available at https://varigg.github.io/humblebundle/
  ```

### Validation

```bash
# Build and serve locally
uv run mkdocs serve
# Visit http://localhost:8000

# Build for deployment
uv run mkdocs build
```

---

## Task D.6: Add Pre-commit Hooks (Comprehensive)

**Priority:** High  
**Estimated Time:** 1 hour  
**Files to Modify:**

- [.pre-commit-config.yaml](../../../.pre-commit-config.yaml)

### Tasks

- [ ] **D.6.1** Create comprehensive pre-commit configuration

  ```yaml
  repos:
    # Ruff - Fast Python linter and formatter
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.12.3
      hooks:
        - id: ruff
          args: [--fix]
        - id: ruff-format

    # Gitleaks - Prevent committing secrets
    - repo: https://github.com/gitleaks/gitleaks
      rev: v8.27.2
      hooks:
        - id: gitleaks

    # Standard pre-commit hooks
    - repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v4.5.0
      hooks:
        - id: trailing-whitespace
        - id: end-of-file-fixer
        - id: check-yaml
        - id: check-toml
        - id: check-json
        - id: check-added-large-files
          args: ["--maxkb=1000"]
        - id: check-merge-conflict
        - id: check-case-conflict
        - id: mixed-line-ending

    # Type checking (optional, can be slow)
    - repo: local
      hooks:
        - id: ty
          name: ty
          entry: uv run ty
          language: system
          types: [python]
          pass_filenames: false
          stages: [manual] # Only run when explicitly called
  ```

- [ ] **D.6.2** Update project to use pre-commit

  ```bash
  uv tool install pre-commit
  pre-commit install
  pre-commit install --hook-type commit-msg  # For conventional commits
  ```

- [ ] **D.6.3** Run pre-commit on all files

  ```bash
  pre-commit run --all-files
  ```

- [ ] **D.6.4** Add pre-commit CI

  ```yaml
  # In .github/workflows/ci.yml, add job:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: pre-commit/action@v3.0.0
  ```

- [ ] **D.6.5** Document pre-commit setup in CONTRIBUTING.md

  ````markdown
  ## Pre-commit Hooks

  This project uses pre-commit hooks to ensure code quality:

  ```bash
  # Install pre-commit
  uv tool install pre-commit

  # Install hooks
  pre-commit install

  # Run manually
  pre-commit run --all-files
  ```
  ````

  Hooks run automatically on `git commit`.

  ```

  ```

### Validation

```bash
# Make a change and commit
echo "test" >> test.txt
git add test.txt
git commit -m "test"
# Should run all hooks
```

---

## Completion Checklist

- [ ] All tasks in D.1 completed (Dependabot)
- [ ] All tasks in D.2 completed (GitHub Actions)
- [ ] All tasks in D.3 completed (Code Coverage)
- [ ] All tasks in D.4 completed (Complexity Metrics)
- [ ] All tasks in D.5 completed (Documentation Site)
- [ ] All tasks in D.6 completed (Pre-commit Hooks)
- [ ] CI pipeline running successfully
- [ ] Code coverage reports generated
- [ ] Documentation site deployed
- [ ] Pre-commit hooks working
- [ ] README updated with badges and links

---

## Ongoing Maintenance Tasks

- [ ] **Weekly:** Review and merge Dependabot PRs
- [ ] **Monthly:** Review code metrics trends
- [ ] **Quarterly:** Update documentation
- [ ] **As needed:** Add new tests to maintain coverage
- [ ] **As needed:** Refactor high-complexity functions
- [ ] **Before releases:** Run full test suite on all platforms

---

## Notes

- Phase D is ongoing - tasks are maintained over the project lifetime
- Automate everything that can be automated
- Monitor metrics to catch quality regressions early
- Keep documentation up to date with code changes
- Use CI to enforce quality standards

---

## Success Metrics

- ✅ All CI checks pass on every commit
- ✅ Code coverage ≥ 80%
- ✅ No functions with complexity > C rating
- ✅ Documentation site accessible and up to date
- ✅ Dependabot PRs merged within 1 week
- ✅ Pre-commit hooks prevent common mistakes

---

## Next Steps

After completing this phase:

1. Continue regular maintenance of tooling
2. Monitor metrics and adjust thresholds as needed
3. Consider additional tools (mutation testing, security scanning)
4. Keep dependencies up to date
5. Iterate on architecture based on usage patterns
