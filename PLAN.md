# Prompt Library — Build Plan

## Product and architecture
Offline-first Windows desktop prompt organizer. Foundation stack: Python 3.12+ with official Qt for Python (PySide6) widgets for a native desktop shell, and SQLite in the per-user application data directory. Keep UI, persistence, and template processing separated; no network service or AI runtime dependency. Pin application dependencies and keep user data/build artifacts out of Git. Windows packaging will use the Qt for Python deployment tooling after the app is stable.

## Milestones
1. **Foundation (active):** runnable app shell, prompt/category/tag data model, durable local storage, removable sample prompts. Storage and UI implementation are present; the storage checks pass, but UI launch is still unverified.
2. **Core:** CRUD, categories/tags/favorites/search/copy, trash/restore, validated versioned JSON backup/import.
3. **Templates and polish:** named placeholders, plain-text/Markdown exchange, shortcuts, unsaved-change protection and UX refinement.
4. **Distribution:** reproducible Windows package, docs, changelog, contribution guide, CI and private GitHub preparation. License decision remains pending.

## Ownership and file boundaries
- Ada: architecture, this plan/status, repository setup and milestone coordination; avoid Lin/Pixel/Rigel implementation paths.
- Lin: `src/prompt_library/data/` (models, SQLite persistence, trash/restore, import/export) and storage-focused docs only.
- Pixel: `src/prompt_library/ui/` and UI entry/shell files only; coordinate against Lin's public data interfaces, do not edit data layer.
- Rigel: `tests/`, packaging/CI files and release verification notes; do not edit app implementation.

## Verification gates
Foundation: launch the shell, initialize a clean local database, inspect sample records, close/reopen and confirm persistence. Core: CRUD, combined filters, trash restore, exact Unicode/code copy, import/export round-trip, malformed import leaves existing data unchanged. Templates: repeated/missing placeholders and unchanged stored template. Distribution: clean Windows package build and actual launch/edit/reopen/copy check where this Windows environment supports it.

## Current status — 2026-11-19
- The project is isolated in `prompt-library/`; the workspace's separate LinkNest files and Git metadata were left untouched.
- Python 3.14.5, PySide6 6.12.0, and pytest are available. The two storage tests and Python source/test compilation pass.
- The UI entry point and three-pane editor are implemented. An offscreen attempt to construct/show `MainWindow` stalled, so desktop launch and interactive behavior remain unverified.
- A Windows GitHub Actions workflow exists at `.github/workflows/windows-build.yml`; it has not run. Build artifact and packaged-app behavior remain unverified.
- GitHub CLI is installed but has no authenticated account; Git CLI is not available. Local project Git initialization and private GitHub repo creation/publication remain outstanding.
