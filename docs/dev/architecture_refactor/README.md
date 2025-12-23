# Architecture Refactoring Plan

This directory contains the comprehensive architecture analysis and refactoring plan for the Humble Tools project. The analysis identifies areas for improvement in separation of concerns, component reuse, code quality, and adherence to Python best practices.

---

## Documents

### Main Analysis

- **[ARCHITECTURE_ANALYSIS.md](ARCHITECTURE_ANALYSIS.md)** - Comprehensive architecture and code quality analysis with detailed findings and recommendations

### Refactoring Phases

The refactoring work is organized into four phases with increasing complexity:

1. **[REFACTOR_A_QUICK_WINS.md](REFACTOR_A_QUICK_WINS.md)** - Quick improvements (1-2 days)

   - Fix type hint inconsistencies
   - Add ruff to pre-commit hooks
   - Standardize widget ID usage
   - Extract common formatting utilities
   - Move CLI-specific display code to track directory

2. **[REFACTOR_B_STRUCTURAL.md](REFACTOR_B_STRUCTURAL.md)** - Structural improvements (3-5 days)

   - Extract BundleDetailsParser class
   - Add database connection lifecycle management
   - Break down large methods
   - Standardize error handling patterns

3. **[REFACTOR_C_ARCHITECTURE.md](REFACTOR_C_ARCHITECTURE.md)** - Architecture refinement (1-2 weeks)

   - Extract DownloadOrchestrator from BundleDetailsScreen
   - Evaluate Database Protocol usage (YAGNI analysis)
   - Migrate to Pydantic for configuration
   - Add type checking with pyright

4. **[REFACTOR_D_TOOLING.md](REFACTOR_D_TOOLING.md)** - Tooling & quality (Ongoing)
   - Set up Dependabot
   - Add GitHub Actions CI/CD
   - Add code coverage reporting
   - Add complexity metrics with radon
   - Set up documentation site with MkDocs
   - Comprehensive pre-commit hooks

---

## Overall Assessment

**Current Score:** 7.5/10  
**Goal:** 9.5/10 after completing all phases

### Key Strengths ✅

- Clear module boundaries (core, sync, track)
- Comprehensive test coverage (130 tests)
- Thread-safe download queue implementation
- Well-designed exception hierarchy
- Constants properly extracted

### Main Improvement Areas 🔧

1. **Code Duplication** - Parsing logic needs extraction
2. **YAGNI Violations** - Some premature abstractions
3. **Separation of Concerns** - UI mixed with business logic in places
4. **Consistency** - Type hints and error handling need standardization
5. **Tooling** - Not fully aligned with project philosophy (ruff, pyright, Pydantic)

---

## How to Use This Plan

### 1. Start with Phase A (Quick Wins)

Phase A provides immediate improvements with minimal risk. Complete all tasks in [REFACTOR_A_QUICK_WINS.md](REFACTOR_A_QUICK_WINS.md) before moving forward.

### 2. Progress Through Phases Sequentially

Each phase builds on the previous one. Complete phases in order:

- Phase A → Phase B → Phase C → Phase D

### 3. Track Progress

Each phase document has a completion checklist at the end. Update the checklist as you complete tasks.

### 4. Commit Strategy

- **Phase A:** Can be one or two commits
- **Phase B:** Break into multiple commits (one per major task)
- **Phase C:** Definitely multiple commits (complex changes)
- **Phase D:** Ongoing commits as tooling is added

### 5. Testing Strategy

Run the full test suite after each task:

```bash
uv run pytest
uv run pytest tests/integration/ -v  # For UI changes
```

---

## Key Architectural Changes

### Display Code Reorganization (Phase A)

**Current Structure:**

```
src/humble_tools/
├── core/
│   └── display.py          # Mix of CLI and shared display code
└── sync/
    └── app.py              # TUI display code
```

**New Structure:**

```
src/humble_tools/
├── core/
│   ├── format_utils.py     # NEW: Shared formatting utilities
│   └── display.py          # Generic display helpers only
├── sync/
│   └── app.py              # TUI display code (unchanged)
└── track/
    ├── commands.py         # CLI commands
    └── display.py          # NEW: CLI-specific display code
```

### Parser Extraction (Phase B)

**Current:** Parsing functions scattered in `humble_wrapper.py`

**New:** Dedicated `BundleDetailsParser` class in `parsers.py`

- Better testability
- Reduced duplication
- Easier to maintain and extend

### Download Orchestration (Phase C)

**Current:** `BundleDetailsScreen` handles everything

**New:** Separate `DownloadOrchestrator` class

- Clean separation of UI and business logic
- Testable without UI
- Reusable download logic

---

## Relationship to App Analysis

This architecture refactoring plan is **separate from** the TUI implementation plan in [../APP_ANALYSIS_AND_REFACTORING.md](../APP_ANALYSIS_AND_REFACTORING.md).

### App Analysis (Phases 1-7)

- Focuses on TUI-specific improvements
- Bug fixes and feature enhancements
- UI/UX improvements
- **Status:** Phases 1-7B complete

### Architecture Refactor (Phases A-D)

- Focuses on overall project architecture
- Code quality and maintainability
- Tooling and automation
- **Status:** Planning complete, implementation pending

Both plans can be worked on in parallel, but **Phase A (Quick Wins) should be prioritized** as it provides foundational improvements that benefit both efforts.

---

## Time Estimates

| Phase   | Duration  | Complexity | Priority |
| ------- | --------- | ---------- | -------- |
| Phase A | 1-2 days  | Low-Medium | High     |
| Phase B | 3-5 days  | Medium     | High     |
| Phase C | 1-2 weeks | High       | Medium   |
| Phase D | Ongoing   | Low-Medium | High     |

**Total Initial Work:** 2-3 weeks for Phases A-C  
**Ongoing Work:** Phase D continues throughout project lifetime

---

## Success Criteria

### Phase A Complete When:

- [ ] All type hints are consistent and complete
- [ ] Ruff is integrated and running in pre-commit
- [ ] Common formatting utilities are extracted
- [ ] CLI display code is in track directory
- [ ] All tests passing

### Phase B Complete When:

- [ ] BundleDetailsParser class is extracted and tested
- [ ] Database connections have proper lifecycle management
- [ ] Large methods are broken down into smaller functions
- [ ] Error handling is standardized across codebase
- [ ] All tests passing

### Phase C Complete When:

- [ ] DownloadOrchestrator is extracted and working
- [ ] Database Protocol decision is made and documented
- [ ] Configuration uses Pydantic with validation
- [ ] Type checking passes with pyright
- [ ] All tests passing

### Phase D Complete When:

- [ ] Dependabot is configured and working
- [ ] GitHub Actions CI/CD is running on all commits
- [ ] Code coverage is ≥80% and reported
- [ ] Complexity metrics are tracked
- [ ] Documentation site is deployed
- [ ] Pre-commit hooks prevent common issues

---

## Questions or Issues?

If you encounter issues during implementation:

1. **Check the analysis document** - Most decisions are explained in [ARCHITECTURE_ANALYSIS.md](ARCHITECTURE_ANALYSIS.md)
2. **Review test coverage** - Tests should guide refactoring
3. **Make incremental changes** - Small commits are easier to review and revert
4. **Update the plan** - If you discover better approaches, document them
5. **Ask for review** - Complex architectural changes benefit from discussion

---

## Philosophy Alignment

This refactoring plan aligns with the project philosophy from [../../.github/copilot-instructions.md](../../.github/copilot-instructions.md):

- ✅ **Simplicity:** Remove unnecessary abstractions (YAGNI)
- ✅ **Modern Tooling:** Add ruff, pyright, Pydantic
- ✅ **Testing:** Maintain high test coverage
- ✅ **Type Safety:** Add comprehensive type hints
- ✅ **Automation:** Pre-commit hooks, CI/CD
- ✅ **Documentation:** MkDocs site for better docs

---

## Next Steps

1. Read [ARCHITECTURE_ANALYSIS.md](ARCHITECTURE_ANALYSIS.md) for full context
2. Start with [REFACTOR_A_QUICK_WINS.md](REFACTOR_A_QUICK_WINS.md)
3. Complete tasks sequentially
4. Update checklists as you progress
5. Commit frequently with descriptive messages
6. Keep tests passing at all times

Good luck! 🚀
