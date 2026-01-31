# CLAUDE.md — Agent Operating Guide (TDD + GitHub + Beads)

## 0) Read First
Before any work, open the current project log and follow “Quick Start for Next Session”:
```bash
cd .projects/specs/<project>
sed -n '1,150p' log.md
```

---

## 1) Source of Truth (Project System)
Active work lives under `.projects/specs/<project>`:

**For Complex Projects** (20+ hours, 10+ tasks, multiple phases):
Use the **project-docs** skill to create the 4-document structure:
- `README.md` — Navigation hub, quick start, status overview (updated: milestones)
- `tasks.md` — Authoritative task specifications (WHAT needs to be done, updated: when planning changes)
- `architecture.md` — System design and requirements (WHY we're building this, updated: when design evolves)
- `log.md` — Session history (WHEN/WHAT HAPPENED, updated: every session)

**Document Authority Model:**
| Document                      | Authority For                    | Updated When     |
| ----------------------------- | -------------------------------- | ---------------- |
| `README.md`                   | Navigation, quick start          | Milestones       |
| `tasks.md`                    | WHAT "done" means                | Planning changes |
| `architecture.md`             | WHY (design decisions)           | Design evolution |
| `log.md`                      | WHEN (session history)           | Every session    |
| Beads (`.beads/issues.jsonl`) | STATUS (open/in_progress/closed) | Real-time        |
| GitHub Issues                 | External tracking, PRs           | Real-time        |

**For Smaller Features** (simple tasks, <20 hours):
- `requirements.md` — WHAT
- `design.md` — HOW + Testing Strategy
- `log.md` — Session tracking

**Task Tracking**:
- Use **Beads** for task status and dependencies (NOT tasks.md)
- Create **GitHub Issues** from Beads (1 bead = 1 issue)
- Use `bd ready` to find next work

**TDD is mandatory** (Red → Green → Refactor). Use `uv run pytest` for all test execution.

```bash
uv venv --python python3.12
source .venv/bin/activate
uv pip install -e .
```

### Using the Project-Docs Skill

**When to Use:**
- Complex projects with 20+ hours of work
- Multiple implementation phases
- 10+ tasks with dependencies
- Need for architecture documentation

**How to Invoke:**
```bash
# Explicit invocation
"Use the project-docs skill to set up documentation for [project name]"

# Or let Claude auto-detect when starting complex projects
```

**What It Creates:**
The skill provides comprehensive guidance and templates for:
1. Initializing the 4-document structure
2. Populating tasks.md during planning
3. Populating architecture.md during design
4. Updating log.md every session
5. Maintaining README.md as navigation hub

**Anti-Patterns to Avoid:**
- ❌ Creating multiple PLAN documents (use architecture.md)
- ❌ Creating multiple TASK documents (use tasks.md)
- ❌ Mixing tasks + architecture in one doc (separate concerns)
- ❌ Deleting historical docs (archive instead)
- ❌ Losing authority model (always document which doc is authoritative for what)

**Templates:**
Skill provides 4 templates at `~/.claude/skills/project-docs/templates/`:
- `README.template.md` (5.4k)
- `tasks.template.md` (3.3k)
- `architecture.template.md` (6.1k)
- `log.template.md` (4.6k)

---

## 2) Task & Issue Conventions (tasks.md → Beads → GitHub Issues)
- **One task == one Bead == one GitHub Issue.**
- **Source of truth**: tasks.md defines all tasks with dependencies
- **Tracking**: Beads tracks status and dependencies in `.beads/issues.jsonl`
- **External visibility**: GitHub Issues for CI/review/collaboration
- **Every task maps to requirements and has tests.**

### Workflow: From tasks.md to Implementation

1. **Define tasks** in tasks.md:
```markdown
### T1: Project Structure & Configuration

**Goal**: Create package structure with pyproject.toml...

**Deliverables**:
- Package directory structure
- pyproject.toml with dependencies

**Test Requirements**:
- Unit: Package imports work
- Integration: MotherDuck connection test

**Acceptance Criteria**:
1) WHEN package installed THEN all modules import
2) WHEN invalid credentials THEN clear error

**Definition of Done**:
- [ ] All tests green
- [ ] ≥95% coverage
- [ ] PR merged; Issue closed

**Dependencies**: None
**Estimate**: Small (4 hours)
```

2. **Create Beads** with dependencies:
```bash
bd create "T1: Project Structure" -t task -p 0 --json
bd create "T2: Core Client" -t task -p 0 --json
bd dep add <T2-id> <T1-id> --type blocks
```

3. **Create GitHub Issues** from ready Beads:
```bash
gh issue create \
  --title "T1: Project Structure & Configuration" \
  --body "See .projects/specs/<project>/tasks.md#T1" \
  --label "project:<project>" --label "type:task" --label "tdd"
```

4. **Link everything**:
- Add GitHub issue number to Bead labels: `gh:#1234`
- Reference in commits: `feat: implement T1 (closes #1234)`

---

## 3) TDD Execution (enforced)
**Always write a failing test first**, then minimal code to pass, then refactor. Keep a green baseline between changes.

```bash
# run whole suite
uv run pytest -q
# focus a subset
uv run pytest -k <name> -v
# coverage gates
uv run pytest --cov=src --cov-report=term-missing
```

Bug-fix and refactor are just two more TDD cycles. No changes without tests.

---

## 4) GitHub + `gh` CLI (authoritative)
**Branching**
```bash
git switch -c feat/<issue>-<slug>
```

**Create an issue for the current task**
```bash
gh issue create \
  --title "T{N}: {Task name from tasks.md}" \
  --body "See .projects/specs/<project>/tasks.md#T{N}" \
  --label "project:<project>" \
  --label "phase:<N>" \
  --label "epic:<epic-name>" \
  --label "type:task" \
  --label "tdd"
```

**PR flow (auto-link issue via Closes)**
```bash
git add -A && git commit -m "test: add failing tests for <task>"
git commit -m "feat: implement <task> to pass tests"
gh pr create --title "feat(<issue>): <task>" --body "Closes #<issue>"
gh pr view --web
gh pr merge --squash --auto
```

After merge: `git pull`, then update `log.md`.

---

## 5) Beads (`bd`) Integration (works with GitHub, not against it)
Beads is a lightweight, **git-backed** local issue DB for agents and humans. We use it to:
- Record/organize discovered work quickly.
- Model dependencies and surface **ready** work.
- Keep state in-repo via JSONL, distributed with git.
- Drive agent/human session continuity.

### Install & Initialize
```bash
brew install beads             # macOS (Homebrew)
bd init                        # initialize in this repo
bd quickstart                  # guided setup
```

### Core Commands We Use
```bash
bd list
bd ready                       # show unblocked, actionable items
bd show <id>
bd update <id> --status in_progress
bd dep add <child> <parent> --type discovered-from
echo ".beads/*.db" >> .gitignore
bd sync -m "Update beads"      # export/commit/pull/import/push
```

### Label Conventions for Large Epics

**Required Labels for ALL Beads/Issues**:
```bash
bd create "T1: Task Name" \
  -t task \
  -p 0 \
  -l "project:<project-name>,phase:<N>,epic:<epic-name>,tdd" \
  -d "Task description with deliverables and estimates"
```

**Label Structure**:
- `project:<name>` — Project identifier (e.g., `project:python-package`, `project:reactor`)
- `phase:<N>` — Phase number (1-6 typically, maps to weeks or logical groupings)
- `epic:<name>` — Epic/theme identifier (same as project for single-epic projects)
- `tdd` — Indicates TDD methodology applies
- `gh:#<num>` — GitHub issue reference (added after issue creation)

**Benefits**:
- Filter by phase: `bd list` shows all beads, filter manually by labels
- Track epic progress: See all tasks for a specific epic
- Parallel work: Identify tasks in different phases that can run concurrently
- Status dashboard: Group by phase to see bottlenecks

### Organizing Large Epics (30+ Tasks)

**Phase Structure** (follow reactor/python-package pattern):

```
Phase 1: Foundation (Week 1)
- T1-T5: Core infrastructure, no dependencies within phase

Phase 2-5: Parallel Feature Tracks (Weeks 2-5)
- Each phase builds on Phase 1
- Tasks within phases may have dependencies
- Some phases can run in parallel (e.g., Structured Output + Embeddings)

Phase 6: Polish & Finalization (Week 5-6)
- T27-T30: Depends on all previous phases
```

**Creating Beads Systematically**:

1. **Create all beads first** (don't set dependencies yet):
```bash
# Phase 1
bd create "T1: Project Structure" -t task -p 0 -l "project:foo,phase:1,epic:foo,tdd" -d "..."
bd create "T2: Core Client" -t task -p 0 -l "project:foo,phase:1,epic:foo,tdd" -d "..."

# Phase 2
bd create "T6: Feature Models" -t task -p 1 -l "project:foo,phase:2,epic:foo,tdd" -d "..."
# ... continue for all 30 tasks
```

2. **Set up dependencies** (use bead IDs from creation):
```bash
# Phase 1: T2-T5 all depend on T1
bd dep add <T2-id> <T1-id> --type blocks
bd dep add <T3-id> <T1-id> --type blocks

# Phase 2: T6 depends on T2, T7 depends on T6, etc.
bd dep add <T6-id> <T2-id> --type blocks
bd dep add <T7-id> <T6-id> --type blocks
```

3. **Verify ready queue**:
```bash
bd ready  # Should show only T1 (no blockers)
```

**Parallel Work Tracks**:

For epics with independent feature tracks, organize phases to enable parallelism:

```
Phase 1: Foundation (T1-T5) → Must complete sequentially
  └─> Unblocks 3 parallel tracks:

Track A: Structured Output (T6-T11)
Track B: Embeddings (T12-T16)
Track C: Registry (T17-T21)

Phase 5: Integration (T22-T26) → Depends on Track A + Track C
Phase 6: Polish (T27-T30) → Depends on all tracks
```

### Linking Beads ↔ GitHub ↔ tasks.md
- Put the **GitHub issue number** in the bead's labels (e.g., `gh:#1234`)
- Reference tasks.md in GitHub issue body
- Keep status synchronized:
  - Claim: `bd update <id> --status in_progress` and assign yourself in the GH issue
  - Close: merge the PR (`Closes #<issue>`), then `bd close <id> --reason implemented`
- Update `log.md` after each session with completed work
- Always `bd sync` before/after a session to keep JSONL and git aligned

> **Why this system?**
> - **tasks.md**: Static reference with full specs (doesn't change during implementation)
> - **Beads**: Dynamic task tracking with dependency reasoning and ready queue (git-backed)
> - **GitHub Issues/PRs**: External review, CI gate, collaboration
> - **log.md**: Session history and next steps
>
> Together they eliminate plan sprawl and lost work.

---

## 6) Unified Loop (TDD + GitHub + Beads)
| Step               | Command(s)                                                               | Outcome                            |
| ------------------ | ------------------------------------------------------------------------ | ---------------------------------- |
| Pick ready work    | `bd ready`, `bd show <id>`                                               | Choose highest-priority ready bead |
| Create GH issue    | `gh issue create --title "T1: ..." --body "See tasks.md#T1"`             | One issue per bead                 |
| Link issue to bead | Add `gh:#1234` label to bead                                             | Bead ↔ GitHub linkage              |
| Claim work         | `bd update <id> --status in_progress` ; assign GH issue                  | Prevents parallel collision        |
| Branch             | `git switch -c feat/<issue>-<slug>`                                      | Work is isolated                   |
| **RED**            | write failing test → `uv run pytest -k <name> -v`                        | Repro and spec                     |
| **GREEN**          | implement minimal code → `uv run pytest`                                 | Pass the tests                     |
| **REFACTOR**       | tidy; keep green → `uv run pytest`                                       | Quality without regressions        |
| Commit/PR          | `git add -A && git commit ...` → `gh pr create --body "Closes #<issue>"` | CI + code review                   |
| Close work         | `gh issue close <num>` ; `bd close <id> --reason implemented`            | Everything reconciled              |
| Sync               | `bd sync` ; `git pull`                                                   | Repo + Beads state aligned         |
| Update docs        | Edit `log.md`                                                            | Session history captured           |

---

## 7) Guardrails
- **No work without tests.** Start from tests; keep a green baseline.
- **Run ty before committing.** Type check Python code before every commit.
- **Update `log.md` each session.** Capture done/next/commits/tests.
- **Use `uv`, not `pip`.** Keep Python/tooling consistent.
- **Keep templates read-only.** Edit only under `.projects/specs/<project>`.
- **Every task has an issue; every issue has tests.**

---

## 8) Minimal Cheatsheets

### Beads
```bash
bd init
bd quickstart
bd create "..." -t task -p 2 --json
bd dep add <child> <parent> --type discovered-from
bd update <id> --status in_progress --json
bd ready
bd dep tree <id>
bd sync -m "Update beads"
```

### GitHub (`gh`)
```bash
gh auth status
gh issue create --title "TN: ..." --body "See tasks.md#TN" \
  --label "project:<project>" --label "type:task" --label "tdd"
gh issue view <#>
gh issue comment <#> -b "Update: <what changed> (<tests>)"
gh pr create --title "feat(<#>): ..." --body "Closes #<#>"
gh pr merge --squash --auto
```

### Tests
```bash
uv run pytest tests/ --quiet
uv run pytest -k <name> -v
uv run pytest --cov=src --cov-report=term-missing
```

### ty (Type Checking)
**ty** is Astral's extremely fast Python type checker (by the makers of Ruff and uv).

```bash
# Run type check on a directory (no installation needed)
uvx ty check llama_party/

# Check specific files
uvx ty check src/main.py src/utils.py

# JSON output for CI
uvx ty check --output-format json

# GitHub Actions format
uvx ty check --output-format github
```

**Pre-commit workflow:**
```bash
# Before committing, always run:
uv run pytest -q           # Tests pass
uvx ty check <path>/       # Type check passes
git add -A && git commit   # Then commit
```

**Fixing type errors:**
- Start with `uvx ty check <path>/` to see all diagnostics
- Fix errors by category (unresolved-import, missing-argument, etc.)
- Use `# type: ignore[rule-name]` sparingly for intentional patterns

**More information:** See the ty skill at `~/.claude/skills/ty/` for:
- `SKILL.md` — Complete usage guide
- `REFERENCE.md` — CLI, configuration, and rules reference
- `examples/` — New project setup and gradual adoption workflows
- `templates/` — pyproject.toml, GitHub Actions, pre-commit configs

---

## 9) Modal (if applicable)
Always run Modal inside the venv:
```bash
source .venv/bin/activate && modal [command]
```
Examples:
```bash
make all
make api-8b
make deploy-batch-processor
make deploy-client
modal deploy data_gen_service/src/queue_service/api.py
```

---

## References
- **ty (type checker)**: `~/.claude/skills/ty/` — Local skill with complete documentation
  - Official docs: https://docs.astral.sh/ty/
- Beads repository docs (read these next):
  - https://github.com/steveyegge/beads/blob/main/QUICKSTART.md
  - https://github.com/steveyegge/beads/blob/main/GIT_WORKFLOW.md
  - https://github.com/steveyegge/beads/blob/main/AGENTS.md
  - https://github.com/steveyegge/beads/blob/main/DESIGN.md
