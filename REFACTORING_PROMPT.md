# Frontend-v2 Refactoring - Work Prompt

Ultrathink

## Objective
Refactor the frontend-v2 codebase to be production-ready, following SOLID, DRY, KISS, and clean architecture principles. All files must be < 500 lines, all methods < 100 lines, with comprehensive unit tests and a unified macOS + D&D design system.

## Your Process

### 1. Read & Understand
- **Read** `PLAN.md` to understand the overall refactoring strategy
- **Read** `PROGRESS.md` to see what has been completed
- **Read** `FRONTEND_REVIEW.md` to understand the issues being addressed
- **Read** the relevant source code in `frontend-v2/src/` to understand current implementation
- **Read** `CLAUDE.md` for backend context and overall project architecture

### 2. Validate
- **Validate** that the task you're about to work on hasn't already been completed (check `PROGRESS.md`)
- **Validate** that the task is still relevant (code may have changed since plan was created)
- **Validate** that you understand the acceptance criteria for the task
- **Validate** any dependencies - does this task require other tasks to be completed first?

### 3. Implement
- **Only then** proceed with implementation
- Follow the coding standards from `CLAUDE.md`:
  - Type safety: Pydantic-style validation, mypy --strict equivalent
  - No `any` types
  - Explicit return types
  - DRY: Extract shared logic to services/utilities
  - SOLID: Single responsibility, dependency injection via container
  - KISS: Simple, clear abstractions
- Write tests alongside code (Phase 5-8 tasks require tests)
- Use design tokens from `styles/core/variables.css` (Phase 1+ tasks)
- Keep methods < 100 lines, files < 500 lines
- Add JSDoc comments for public APIs

### 4. Update Progress
- **Update** `PROGRESS.md` after completing each task
- Mark tasks as complete with `[x]`
- Update phase completion percentages
- Update "Last Updated" date
- Add any notes about decisions or deviations

## Example Workflow

```
User: "Work on Phase 1.1 - Create design token system"

You:
1. Read PLAN.md Phase 1.1 to see what's required
2. Read PROGRESS.md to confirm it's not done
3. Read existing styles/main.css to understand current color/spacing usage
4. Validate that no one has started this (check for styles/core/ directory)
5. Create styles/core/variables.css with comprehensive design tokens
6. Create other core CSS files (reset, utilities, typography)
7. Update PROGRESS.md to mark 1.1 tasks as complete
```

## Key Rules

- ❌ **Never skip validation** - always read code and progress before implementing
- ❌ **Never assume** - if unsure, ask clarifying questions
- ✅ **Always update PROGRESS.md** - keep tracking current
- ✅ **Always follow CLAUDE.md standards** - type safety, SOLID, DRY, KISS
- ✅ **Always test** - write unit tests for new code
- ✅ **Always use design tokens** - no hardcoded colors/spacing after Phase 1

## Questions to Ask Yourself

Before implementing:
- [ ] Have I read the relevant parts of PLAN.md?
- [ ] Have I checked PROGRESS.md for completion status?
- [ ] Have I read the existing code I'll be modifying?
- [ ] Do I understand what "done" looks like for this task?
- [ ] Are there any dependencies I need to complete first?
- [ ] Will this change break existing functionality?

After implementing:
- [ ] Does this follow SOLID/DRY/KISS principles?
- [ ] Are all files < 500 lines and methods < 100 lines?
- [ ] Are there tests (if applicable)?
- [ ] Have I used design tokens instead of hardcoded values?
- [ ] Have I updated PROGRESS.md?
- [ ] Does this work end-to-end (tested manually if UI)?

## Ready to Start?

Pick a task from `PLAN.md`, follow the 4-step process above, and let's build a production-ready frontend! 🚀
