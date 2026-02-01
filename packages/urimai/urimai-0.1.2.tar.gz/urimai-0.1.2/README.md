# urimai

AI-powered SQL answer engine — ask questions about your databases using AI.

## Installation

```bash
# From PyPI
pip install urimai

# From source
git clone https://github.com/shivakharbanda/urimAI
cd urimAI
uv sync
```

## Quick Start

```bash
urim setup              # First-time config wizard
urim init ./chinook.db  # Register a database
urim chat chinook       # Start chatting
```

## Commands

| Command | Description |
|---------|-------------|
| `urim setup` | Run first-time setup wizard (provider, API key, name) |
| `urim init <path>` | Register a SQLite database or CSV file |
| `urim list` | List all registered databases |
| `urim chat <db_name>` | Start interactive chat session |
| `urim sync <db_name>` | Re-sync database schema metadata |
| `urim config [key] [value]` | View or modify settings |
| `urim export <db_name>` | Export data dictionary (xlsx/markdown) |

### `urim setup`

Run the first-time setup wizard to configure your AI provider, API key, and display name.

### `urim init <path>`

Register a SQLite database or CSV file. CSV files are automatically converted to SQLite with LLM-powered schema inference.

```bash
urim init ./my_database.db
urim init ./data.csv --name my_data --table-name sales --delimiter "," --encoding utf-8
```

| Option | Description |
|--------|-------------|
| `--name` | Custom name for the database (default: filename) |
| `--table-name` | Table name for CSV import (default: LLM-suggested) |
| `--delimiter` | CSV delimiter character (default: `,`) |
| `--encoding` | CSV file encoding (default: `utf-8`) |

### `urim list`

List all registered databases.

```bash
urim list
```

### `urim chat <db_name>`

Start an interactive chat session with a registered database.

```bash
urim chat chinook
```

### `urim sync <db_name>`

Re-sync schema metadata for a registered database. Useful after the source data changes.

```bash
urim sync chinook
```

### `urim config [key] [value]`

View or modify configuration settings.

```bash
urim config                          # Show all settings
urim config provider.default openai  # Set default provider
urim config --reset                  # Reset to defaults
urim config --path                   # Show directory paths
```

| Option | Description |
|--------|-------------|
| `--reset` | Reset config to defaults |
| `--path` | Show config/data directory paths |
| (no args) | Show all current settings |

### `urim export <db_name>`

Export data dictionary for a registered database.

```bash
urim export chinook
urim export chinook -f markdown -o chinook_dict.md
urim export chinook --include-sample-data
```

| Option | Description |
|--------|-------------|
| `--format` / `-f` | Output format: `xlsx` or `markdown` (default: `xlsx`) |
| `--output` / `-o` | Output file path |
| `--include-sample-data` | Include sample data rows (default: off) |
| `--include-profile` | Include column profile statistics (default: on) |
| `--include-quality` | Include quality report data (default: on) |

### Global option

| Option | Description |
|--------|-------------|
| `--model <provider>` | Override the default AI provider for a single command |

## Configuration

- **Config file**: `~/.urimai/config.toml`
- **API keys**: stored in the system keyring, or set via environment variables (`GOOGLE_API_KEY`, `OPENAI_API_KEY`)
- **Supported providers**: Google Gemini, OpenAI

## License

[Elastic License 2.0 (ELv2)](LICENSE)
