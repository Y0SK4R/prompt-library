# QA and Release Status — 2026-11-19

## Result

The packaged Windows application launches and renders. The prompt list initially occupied only 97 px in an 1180 px window, clipping prompt titles; it now occupies 321 px after an initial splitter sizing fix. Source tests and compilation pass, and a separate packaged build succeeded. This is a local QA result, not a release verification.

## Checks run — 2026-11-19

- `python -m pytest -q tests` — **4 passed**, including dirty-navigation and splitter-width regressions.
- `python -m compileall -q src tests` — passed.
- PyInstaller 6.22.3 build to `build/qa-dist/PromptLibrary.exe` — succeeded on Windows 11 / Python 3.14.5.
- Default `dist/PromptLibrary.exe` rebuild — blocked because the original running app held the executable open. The original app and its database were left untouched; the QA build was written to a separate folder.
- Launched the QA executable with an isolated `%LOCALAPPDATA%` folder. At 1180 px window width, the rendered category, prompt, and editor panes measured 200 px, 321 px, and 615 px respectively.
- In the UI, created and saved a prompt with tags and a Unicode body. Read back the temporary SQLite database and confirmed the prompt, body metadata, tags, and active state.
- Exercised edit/save/reopen selection and the trash action in the prior packaged build. Storage tests cover persistence, trash/restore, JSON round-trip, and invalid-import atomicity.

## Fix made

The horizontal splitter now starts with widths `[200, 360, 588]`. Previously its default size hints left the prompt list at 97 px in the standard 1180 px window.

## UI scope gaps and remaining verification

- The UI has no category creation, JSON import, or JSON export controls. These operations exist in the storage layer and JSON behavior is covered by storage tests, but the corresponding packaged user flows cannot be exercised.
- Restore was not verified through the packaged UI. Storage-level trash/restore tests pass.
- Packaged close-and-reopen persistence and backup recovery through normal user flows remain unverified.
- `dist/PromptLibrary.exe` was not rebuilt because it was in use. The separate QA artifact is `build/qa-dist/PromptLibrary.exe`; it is not a published release.
- The executable is unsigned and has not been tested on a second Windows computer. The GitHub workflow was not run, nothing was published, and no license has been selected.

The app stores user data at `%LOCALAPPDATA%\PromptLibrary\prompts.sqlite3`. The interactive QA run used a temporary local data folder.
