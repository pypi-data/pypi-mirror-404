# urimai

[![PyPI version](https://img.shields.io/pypi/v/urimai)](https://pypi.org/project/urimai/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: ELv2](https://img.shields.io/badge/license-ELv2-green)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-readthedocs-blue)](https://urimai.readthedocs.io/en/latest/)

**AI-powered SQL answer engine** — ask questions about your databases in plain English.

## What is urimai?

urimai lets you query SQLite databases and CSV files using natural language.
Point it at your data, ask a question, and urimai figures out the right SQL,
runs it, and explains the results. It also profiles your columns and runs
data-quality checks automatically when you register a database, so you can
understand your dataset before you start exploring.

## Key features

- **Natural language SQL** — ask questions in plain English, get SQL + results + explanations
- **CSV import** — drop in a CSV file and urimai converts it to SQLite with LLM-powered schema inference
- **Data profiling** — automatic column-level statistics (min, max, nulls, distributions)
- **Quality checks** — data-quality rules generated and evaluated by the LLM
- **Export** — data dictionaries in Excel or Markdown
- **Multi-provider LLM** — supports Google Gemini and OpenAI out of the box

## Requirements

- **Python 3.11 or later** — [download here](https://www.python.org/downloads/)
- An API key from [Google Gemini](https://aistudio.google.com/apikey) or [OpenAI](https://platform.openai.com/api-keys)

## Quick start

```bash
pip install urimai        # install from PyPI
urim setup                # configure your API provider and key
urim init ./mydata.db     # register a SQLite database (or CSV)
urim chat mydata          # start asking questions
```

## Command reference

| Command | Description |
|---------|-------------|
| `urim setup` | First-time setup wizard (provider, API key, name) |
| `urim init <path>` | Register a SQLite database or CSV file |
| `urim list` | List all registered databases |
| `urim chat <name>` | Interactive chat session with a database |
| `urim sync <name>` | Re-sync schema metadata after data changes |
| `urim config [key] [value]` | View or modify settings |
| `urim export <name>` | Export data dictionary (xlsx or markdown) |

## Links

- **Documentation**: <https://urimai.readthedocs.io/en/latest/>
- **PyPI**: <https://pypi.org/project/urimai/>
- **Source**: <https://github.com/shivakharbanda/urimAI>

## License

urimai is licensed under the [Elastic License 2.0 (ELv2)](LICENSE). You are free
to use, copy, distribute, and modify the software for any purpose **except**
providing it as a managed service to third parties. See the LICENSE file for full
terms.

## Contributing

Contributions are welcome! See the [developer guide](https://urimai.readthedocs.io/en/latest/contributing.html) for setup instructions and project architecture.
