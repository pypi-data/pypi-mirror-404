# SQL Answer Engine

Ask natural-language questions about SQLite databases and CSV files using AI.

## Prerequisites

- Python >= 3.11.6
- [uv](https://docs.astral.sh/uv/) package manager
- A Google API key (Gemini)

## Installation

```bash
git clone <repo-url>
cd sql_answer_engine
uv sync
```

Create a `.env` file in the project root:

```
GOOGLE_API_KEY=your-google-api-key
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | Yes | — | Google Gemini API key |
| `MODEL_NAME` | No | `gemini-2.5-flash` | Model to use for AI queries |
| `METADATA_DB_PATH` | No | `./metadata.db` | Path to the internal metadata database |
| `DEFAULT_SAMPLE_ROWS` | No | `5` | Number of sample rows extracted per table during init/sync |

## CLI Commands

### `sql-engine init <path>`

Register a SQLite database or CSV file.

```bash
sql-engine init ./my_database.db
sql-engine init ./data.csv --name my_data --table-name sales --delimiter "," --encoding utf-8
```

| Option | Description |
|---|---|
| `--name` | Custom name for the database (default: filename) |
| `--table-name` | Table name for CSV import (default: LLM-suggested) |
| `--delimiter` | CSV delimiter character (default: `,`) |
| `--encoding` | CSV file encoding (default: `utf-8`) |

CSV files are automatically converted to SQLite with LLM-powered schema inference.

### `sql-engine list`

List all registered databases.

```bash
sql-engine list
```

### `sql-engine chat <db_name>`

Start an interactive chat session with a registered database.

```bash
sql-engine chat my_database
```

### `sql-engine sync <db_name>`

Re-sync schema metadata for a registered database. Useful after the source data changes.

```bash
sql-engine sync my_database
```

### `sql-engine config`

View or modify settings.

```bash
sql-engine config --show
sql-engine config --sample-rows 10
```

| Option | Description |
|---|---|
| `--show` | Show current settings |
| `--sample-rows` | Set number of sample rows extracted per table |

## Quick Start

```bash
# Register a database
sql-engine init ./chinook.db

# Start chatting
sql-engine chat chinook
```
