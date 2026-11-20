# Prompt Library

A simple offline Windows app for saving, organizing, searching, and reusing prompts of any kind.

## Download for Windows

The project does not have a published GitHub release yet. You can build the executable from source using the instructions below. Once a release is published, its download will be listed on the [Releases page](https://github.com/Y0SK4R/prompt-library/releases). The unsigned build may show a Microsoft Defender SmartScreen notice on first launch.

The app keeps your collection at `%LOCALAPPDATA%\PromptLibrary\prompts.sqlite3`. Updating or replacing the app does not delete your prompts. JSON backup import and export are not available from the current interface yet.

## Features

- Create and edit prompts with a title, description, tags, and favorite status; assign an existing category. Category creation is not available from the current interface yet.
- Search prompt titles, descriptions, body text, and tags.
- Copy a prompt, or fill `{{placeholders}}` before copying.
- Move prompts to trash and restore them later.
- The storage layer supports versioned JSON import/export and Markdown export, but the current interface has no controls for these operations.
- Store data locally in SQLite; no account or network connection is required.

## Run from source

Requires Windows and Python 3.12 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = 'src'
python -m prompt_library
```

## Build the Windows executable

```powershell
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --windowed --onefile --name PromptLibrary --paths src src/prompt_library/__main__.py
```

The executable will be at `dist\PromptLibrary.exe`. A GitHub Actions workflow is configured to test and build the executable on pushes to `main`; its artifact is attached to the workflow run. A version tag such as `v0.1.0` is configured to create a GitHub release with the executable attached. These steps require the workflow to be present and enabled in the published repository.

## Tests

```powershell
$env:PYTHONPATH = 'src'
python -m pytest -q tests
```

## Privacy and license

Prompt Library works offline. Your prompts are stored on your computer; do not commit personal prompt collections or database files to this repository.

This repository currently has no license. Until the owner chooses and adds one, public visibility does not grant permission to reuse or redistribute the code. The Windows executable has not been code-signed or tested on a second computer.

