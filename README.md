# Prompt Library

Prompt Library is an offline Windows desktop app for saving, organizing, searching, and reusing chatbot prompts, instruction prompts, and skill text.

## Current status

The project is in its foundation milestone. It includes a SQLite storage layer, categories and tags, filtering, trash and restore, JSON/Markdown transfer, a PySide6 desktop interface, storage tests, and a Windows build workflow. The desktop interface and packaged Windows app have not yet been verified; see [QA_STATUS.md](QA_STATUS.md).

## Run from source

Requires Python 3.12 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = 'src'
python -m prompt_library
```

Run the storage tests with:

```powershell
$env:PYTHONPATH = 'src'
python -m pytest -q tests
```

## Data and privacy

The app is designed to work offline and does not require an AI account, API key, or hosted backend. Keep your prompt collection and backups private; the repository contains application source, not a place to store personal prompts.

## License

No license has been selected yet. Until one is added, the source is publicly viewable but reuse and redistribution are not granted by an open-source license.
