# Portfolio Management

> A Python package for building optimal ETF portfolios

[![Python](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/)
[![Typed](https://img.shields.io/badge/typed-pydantic%20v2-informational.svg)](https://docs.pydantic.dev/)
[![ORM](https://img.shields.io/badge/orm-SQLAlchemy%202.0-red.svg)](https://www.sqlalchemy.org/)
[![CLI](https://img.shields.io/badge/cli-Typer-green.svg)](https://typer.tiangolo.com/)()
[![Tests](https://img.shields.io/badge/tests-pytest-yellow.svg)](https://docs.pytest.org/)

## Overview

This project is a Python package for building optimal ETF portfolios. As a baseline, I plan on implementing a mean-variance optimization tool, with retrieval of historical price data from a third-party provider ([EODHD](https://eodhd.com/)). In the future, I would also allow for factor analysis (Fama-French 3-factor model), and for filtering of assets based on ESG scores.

Please note that this is a personal project, made mostly for fun. I am not a professional financial advisor, and any decisions made based on this software are your own responsibility. Use at your own risk :). 

## Features implemented so far

- **Retrieval of global exchanges:** fetches the full list of exchanges from EODHD and stores them in a local SQLite database.
- **Seeded ETF assets:** a curated list of ETFs is preloaded into the database for experimentation.
- **Tests:** unit tests cover the client, repositories, and CLI commands.

## Features I swear I will implement in the future

- **CLI-managed asset list:** Allow the user to add and remove tracked assets from the command line
- **Asset price ingestion:** Retrieve historical price series for tracked ETFs from EODHD and store them in the database
- **Mean-variance optimization:** Calculate expected return, variance, and efficient allocation for a given set of ETFs

## Features I might implement in the future

- **Factor analysis:** 
  - Fama-French 3-factor model
  - Potentially extend to additional factors
- **ESG filtering:** Allow the user to filter ETFs based on ESG scores
  - Don't really know how to get ESG scores easily, how to filter by industry, etc.
  - I want to avoid relying on expensive APIs...
- **Vulgarization:** 
  - Provide easy-to-understand explanations of the financial concepts and models used in the package, so that users can learn while they use it
  - Explain the limitations and assumptions of the models, so that users can make informed decisions

## Architecture

```
src/portfolio_management/
├── clients/                  # Third-party API clients (EODHD)
├── cli/                      # Typer command-line entrypoints
│   ├── seed_db.py                # Seed the database with base ETF assets
│   └── get_exchanges.py          # Fetch & store exchanges from EODHD
├── core/                     # Settings (pydantic-settings) and constants
├── database/                 # SQLAlchemy engine, ORM models, and repositories
│   └── repos/                # Data-access layer (repository pattern)
└── models.py                 # Pydantic domain models (AssetModel, ExchangeModel)
```

## Tech Stack

| Concern            | Tool                          |
| ------------------ | ----------------------------- |
| Language           | Python 3.14+                  |
| Packaging / env    | [uv](https://docs.astral.sh/uv/) + Hatchling |
| Validation / models| Pydantic v2, pydantic-settings|
| Persistence        | SQLAlchemy 2.0 (SQLite)       |
| CLI                | Typer                         |
| HTTP               | requests                      |
| Testing            | pytest                        |

## Getting Started

### Prerequisites

- Python **3.14+**
- [uv](https://docs.astral.sh/uv/) for dependency management
- An [EODHD API key](https://eodhd.com/) for fetching market data

### Installation

```bash
git clone https://github.com/LucieBois/portfolio_management.git
cd portfolio_management
uv sync
```

### Configuration

Create a `.env` file at the project root (see `.env.example`):

```dotenv
EODHD_API_KEY=your_api_key_here
DB_PATH=database.sqlite
```

## Usage

**Seed the database** with the base set of ETF assets:

```bash
uv run seed-db
```

**Fetch and store the list of exchanges** from EODHD:

```bash
uv run get-exchanges
```

Use `--dry-run` to fetch data without writing to the database:

```bash
uv run get-exchanges --dry-run
```

## Testing

```bash
uv run pytest
```

## License

All rights reserved.
