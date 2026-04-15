# Phase 4: Profile Globals Refactor

**Purpose**: Replace the 11 mutable module-level globals in `helpers/profile/profile.py` with a clean `ProfileConfig` dataclass. This is the largest structural change and touches ~10 files. Plan this as a dedicated session.

**Prerequisite**: Phases 1–3 (all foundation, separation, and safety work should be done first)

| # | Task | Audit ID | Effort | Files |
|---|------|----------|--------|-------|
| 23 | [Replace profile globals with ProfileConfig](23-profile-config-dataclass.md) | C-01 | Large | ~10 files |
| 24 | [Defer profile initialization](24-defer-profile-init.md) | C-02 | Medium | profile.py, cli.py, gui.py |
| 25 | [Add migration version check](25-migration-version-check.md) | C-15 | Small | contract.py, serializer.py |

## Ordering Notes

- **Task 23 is the hardest item in the entire audit.** It touches every file that imports profile globals. Plan carefully.
- Task 24 depends on Task 23 — the deferred init pattern works best with the new ProfileConfig.
- Task 25 is independent and can be done before or after Tasks 23–24.

## Risk Mitigation

- Before starting Task 23, run `grep -r "from helpers.profile.profile import\|from helpers.profile import profile\|import helpers.profile.profile" --include="*.py"` to get the complete list of consumer files.
- Make the change backward-compatible: keep the old globals as aliases initially, then deprecate them.
- Test after each file is updated — not in a single batch commit.
