# Stanley's Raft

A local-first Python dynamic-memory prototype.

The project provides structured memory capture, versioned SQLite
persistence, retrieval, context assembly, and provider-neutral
model response integration.

## Requirements

- Python 3.10 or newer.
- Pydantic 2.14.3.
- SQLite, provided through Python's standard library.
- Ollama is optional for local model response integration.

## Python environment

From the repository root, in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If the Python launcher selects an unsuitable interpreter, specify an
installed Python 3.10-or-newer version explicitly.

## Initialize a fresh database

The application expects its SQLite database to exist already.
It does not initialize the schema automatically.

The following creates a new local database and refuses to overwrite
an existing one:

```python
from pathlib import Path
import sqlite3

database = Path("data/dm_memory.db")
database.parent.mkdir(parents=True, exist_ok=True)

if database.exists():
    raise SystemExit(
        f"Refusing to overwrite existing database: {database}"
    )

connection = sqlite3.connect(database)
try:
    schema = Path("src/dynamic_memory/schema.sql").read_text(
        encoding="utf-8"
    )
    connection.executescript(schema)
finally:
    connection.close()

print(f"Initialized database: {database}")
```

Save this as a temporary local setup script or run it from a Python
session. Do not commit local database files.

## Optional local model integration

The default Ollama model configured by the adapter is:

`qwen2.5:14b`

Install and start Ollama separately, then retrieve the model:

```powershell
ollama pull qwen2.5:14b
```

Ollama is not a Python package and is not installed by
`requirements.txt`.

## Project boundaries

- Extraction proposes candidates; it does not automatically capture
  or persist them.
- Capture is an explicit operation.
- Model responses are not persisted by the current workflow.
- The application uses SQLite and the existing five-table schema.
- The included B03/B04 evidence documents the completed scope and
  its stated limitations.

Live Ollama acceptance and persistence across an actual application
restart are not claimed by the existing B03/B04 test evidence.

This repository is a development prototype, not a claim of
production readiness.