# MySQL to Google Sheets Sync

[![CI](https://github.com/BrandonFricke/mysql-to-sheets/actions/workflows/ci.yml/badge.svg)](https://github.com/BrandonFricke/mysql-to-sheets/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/mysql-to-sheets)](https://pypi.org/project/mysql-to-sheets/)
[![Python versions](https://img.shields.io/pypi/pyversions/mysql-to-sheets)](https://pypi.org/project/mysql-to-sheets/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![codecov](https://codecov.io/gh/BrandonFricke/mysql-to-sheets/graph/badge.svg)](https://codecov.io/gh/BrandonFricke/mysql-to-sheets)

A Python ETL package that synchronizes data from SQL databases to Google Sheets using Service Account authentication. Supports MySQL, PostgreSQL, SQLite, and SQL Server with four access interfaces: CLI, REST API, Web Dashboard, and Desktop Application.

**Version:** 1.0.0 | **Python:** 3.10-3.12+ | **License:** MIT

## Features

- **Multi-database support** — MySQL, PostgreSQL, SQLite, SQL Server
- **Multiple sync modes** — full replace, append, and streaming (chunked) for large datasets
- **Interactive setup wizard** — `quickstart` command walks through first-time configuration
- **Demo mode** — try it without a real database (`--demo`)
- **REST API** (FastAPI) with OpenAPI docs at `/docs`
- **Web Dashboard** (Flask) for browser-based sync management
- **Built-in scheduler** — cron-based scheduling with APScheduler
- **Column mapping** — rename, reorder, and filter columns
- **Preview & dry-run** — see diffs before applying changes
- **Snapshots & rollback** — restore previous sheet states
- **Incremental sync** — timestamp-based change detection
- **Job queue** — async job processing with SQLite or Redis backends
- **Freshness/SLA monitoring** — track data staleness with alerts
- **Multi-tenant** — organizations, users, RBAC (owner/admin/operator/viewer)
- **Notifications** — email, Slack, and webhook backends
- **Prometheus metrics** — built-in metrics endpoint
- **Subscription tiers** — FREE, PRO, BUSINESS, ENTERPRISE with usage metering
- **RS256 license keys** — offline-validated JWT license keys

## Architecture

```mermaid
graph TD
    CLI["CLI (argparse)"] --> Core
    API["REST API (FastAPI)"] --> Core
    Web["Web Dashboard (Flask)"] --> Core
    Desktop["Desktop (PyInstaller)"] --> Core

    Core["Core ETL<br/>fetch → clean → push"] --> DB["Database<br/>MySQL · PostgreSQL<br/>SQLite · SQL Server"]
    Core --> Sheets["Google Sheets<br/>(gspread)"]
    Core --> Notify["Notifications<br/>Email · Slack · Webhook"]

    Core -.-> Scheduler["Scheduler<br/>(APScheduler)"]
    Core -.-> Jobs["Job Queue<br/>SQLite · Redis"]
    Core -.-> Snapshots["Snapshots<br/>& Rollback"]
```

## Getting Started

### Try It First (No Setup Required)

```bash
pip install mysql-to-sheets
mysql-to-sheets sync --demo
```

This runs a sample sync with built-in demo data. See [Demo Mode](docs/demo.md) for details.

### Full Setup

Ready to sync real data:

#### Step 1: Install

```bash
pip install mysql-to-sheets
```

#### Step 2: Set Up Google Cloud

1. Create a service account: [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Download JSON key as `service_account.json`
3. Enable Google Sheets API: [Enable API](https://console.cloud.google.com/apis/library/sheets.googleapis.com)

[Detailed Setup Guide](docs/google-cloud-setup.md)

#### Step 3: Configure

```bash
mysql-to-sheets quickstart
```

Or create `.env` manually:

```bash
DB_HOST=localhost
DB_USER=readonly_user
DB_PASSWORD=secret
DB_NAME=mydb
SQL_QUERY=SELECT * FROM users LIMIT 1000
GOOGLE_SHEET_ID=your_spreadsheet_id
SERVICE_ACCOUNT_FILE=./service_account.json
```

#### Step 4: Sync

```bash
# Preview changes first
mysql-to-sheets sync --dry-run

# Run the sync
mysql-to-sheets sync
```

### Troubleshooting

If something goes wrong:

```bash
mysql-to-sheets diagnose
```

[Troubleshooting Guide](docs/troubleshooting.md)

### Optional Dependencies

```bash
pip install mysql-to-sheets[postgres]   # PostgreSQL support
pip install mysql-to-sheets[mssql]      # SQL Server support
pip install mysql-to-sheets[redis]      # Redis job queue backend
pip install mysql-to-sheets[desktop]    # Desktop app dependencies
pip install mysql-to-sheets[all]        # All optional drivers
```

### Try Without Setup

Demo mode requires no database or Google Sheets:

```bash
mysql-to-sheets sync --demo
```

### Development Install

```bash
git clone https://github.com/BrandonFricke/mysql-to-sheets.git
cd mysql-to-sheets
pip install -e ".[dev]"
```

> **Desktop users:** Download the latest installer from [GitHub Releases](https://github.com/BrandonFricke/mysql-to-sheets/releases):
> - **macOS:** `mysql-to-sheets-X.X.X-macos.dmg` — drag to Applications
> - **Windows:** `mysql-to-sheets-X.X.X-windows-setup.exe` — standard installer
> - **Linux:** `mysql-to-sheets-X.X.X-x86_64.AppImage` — portable, no installation needed
>
> See [Desktop Installation](#desktop-installation) for security warning bypass instructions.
>
> **Developing from source?** Clone the repo, run `pip install -r requirements.txt`, and use `python -m mysql_to_sheets` instead.

## Access Interfaces

### CLI

```bash
python -m mysql_to_sheets sync                     # Run sync
python -m mysql_to_sheets sync --preview           # Show diff before applying
python -m mysql_to_sheets sync --dry-run           # Validate without pushing
python -m mysql_to_sheets sync --db-type=postgres  # Use PostgreSQL
python -m mysql_to_sheets validate                 # Check configuration
python -m mysql_to_sheets diagnose                 # Full system diagnostics
```

### REST API (FastAPI — port 8000)

```bash
uvicorn mysql_to_sheets.api.app:app --reload --port 8000
# Swagger docs at http://localhost:8000/docs
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sync` | Run sync operation |
| POST | `/api/v1/validate` | Validate configuration |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/history` | Sync history |
| GET/POST | `/api/v1/schedules` | Schedule management |
| GET | `/api/v1/freshness` | SLA monitoring |
| GET | `/api/v1/jobs` | Job queue status |
| GET | `/metrics` | Prometheus metrics |

### Web Dashboard (Flask — port 5000)

```bash
flask --app mysql_to_sheets.web.app run --port 5000
```

Provides a browser-based interface for sync management, schedule configuration, job monitoring, snapshot/rollback, and diagnostics.

### Monitoring (Prometheus + Grafana)

```bash
# Start API with Prometheus and Grafana
docker compose --profile monitoring up

# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000 (admin/admin)
```

Pre-configured with auto-provisioned datasource, alert rules, and dashboard.

## Supported Databases

| Database | `DB_TYPE` | Default Port | Driver |
|----------|-----------|-------------|--------|
| MySQL | `mysql` | 3306 | mysql-connector-python |
| PostgreSQL | `postgres` | 5432 | psycopg2-binary |
| SQLite | `sqlite` | — | built-in |
| SQL Server | `mssql` | 1433 | pymssql |

```bash
# Examples
python -m mysql_to_sheets sync --db-type=mysql     # default
python -m mysql_to_sheets sync --db-type=postgres
python -m mysql_to_sheets sync --db-type=sqlite
python -m mysql_to_sheets sync --db-type=mssql
```

You can also use a `DATABASE_URL` connection URI instead of individual variables:

```bash
DATABASE_URL=postgres://user:pass@localhost:5432/mydb
```

## Configuration

Copy `.env.example` to `.env` and set the required variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DB_USER` | Yes | Database username |
| `DB_PASSWORD` | Yes | Database password |
| `DB_NAME` | Yes | Database name (or file path for SQLite) |
| `GOOGLE_SHEET_ID` | Yes | Target spreadsheet ID or full URL |
| `SQL_QUERY` | Yes | SQL query to execute |

Optional variables cover database host/port, SSL, connection pooling, worksheet management, notifications, scheduling, and more. See `.env.example` for the full list.

## Sync Modes

| Mode | Flag | Description |
|------|------|-------------|
| Replace | (default) | Clear sheet, push all data — best for full refresh |
| Append | `--mode=append` | Add rows without clearing — for incremental additions |
| Streaming | `--mode=streaming --chunk-size=500` | Process in chunks — for large datasets (>10k rows) |

Additional options:

```bash
python -m mysql_to_sheets sync --preview           # Show diff before applying
python -m mysql_to_sheets sync --incremental       # Only sync changed rows
python -m mysql_to_sheets sync --create-worksheet  # Auto-create missing tab
python -m mysql_to_sheets sync --column-case=title # Transform column names
```

## Common Commands

```bash
# Sync
python -m mysql_to_sheets sync
python -m mysql_to_sheets sync --demo
python -m mysql_to_sheets sync --dry-run
python -m mysql_to_sheets sync --preview --output=json

# Setup & diagnostics
python -m mysql_to_sheets quickstart
python -m mysql_to_sheets validate
python -m mysql_to_sheets test-db --diagnose
python -m mysql_to_sheets test-sheets --diagnose
python -m mysql_to_sheets diagnose

# Worksheets
mysql-to-sheets sheet list
mysql-to-sheets sheet create --name="Data Export"

# Scheduling
mysql-to-sheets schedule add --name="daily" --cron="0 6 * * *"
mysql-to-sheets schedule list
mysql-to-sheets schedule run

# Snapshots
python -m mysql_to_sheets snapshot create --name="Before update"
python -m mysql_to_sheets rollback --snapshot-id=1

# Database migrations
mysql-to-sheets db upgrade
```

## Project Structure

```
mysql-to-sheets/
├── mysql_to_sheets/           # Main package
│   ├── core/                  # Business logic (40+ modules)
│   │   ├── config.py          # Config dataclass with singleton
│   │   ├── sync.py            # SyncService + ETL functions
│   │   ├── exceptions.py      # Error hierarchy with codes
│   │   ├── database/          # MySQL/PostgreSQL/SQLite/MSSQL
│   │   ├── notifications/     # Email, Slack, webhook
│   │   ├── scheduler/         # APScheduler integration
│   │   └── webhooks/          # Webhook delivery
│   ├── cli/                   # Command-line interface (25 commands)
│   ├── api/                   # FastAPI REST API
│   │   ├── app.py             # Application factory
│   │   ├── routes.py          # Main router
│   │   └── middleware/        # Auth, rate limiting, CORS, RBAC
│   ├── web/                   # Flask web dashboard
│   │   ├── app.py             # Application factory
│   │   ├── blueprints/        # Route handlers (12 blueprints)
│   │   └── templates/         # Jinja2 templates (23 templates)
│   ├── models/                # SQLAlchemy models (17 models)
│   └── desktop/               # PyInstaller desktop app
├── tests/                     # Test suite (57 test files)
├── alembic/                   # Database migrations
├── helm/                      # Kubernetes Helm chart
├── monitoring/                # Prometheus alerts + Grafana dashboards
├── .env.example               # Configuration template
├── requirements.txt           # Python dependencies
└── pyproject.toml             # Package config (ruff, mypy, pytest)
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
pytest --cov=mysql_to_sheets

# Lint
ruff check mysql_to_sheets

# Type check
mypy mysql_to_sheets
```

## Desktop Installation

Download the installer for your platform from [GitHub Releases](https://github.com/BrandonFricke/mysql-to-sheets/releases).

### macOS

1. Download `mysql-to-sheets-X.X.X-macos.dmg`
2. Open the DMG and drag "MySQL to Sheets Sync" to Applications
3. On first launch, you may see a security warning (app is not notarized)

**Bypassing macOS Gatekeeper:**
1. Right-click (or Ctrl+click) the app in Applications
2. Select "Open" from the context menu
3. Click "Open" in the dialog
4. The app will launch and be remembered for future launches

### Windows

1. Download `mysql-to-sheets-X.X.X-windows-setup.exe`
2. Run the installer — it will create Start Menu shortcuts
3. On first launch, you may see a SmartScreen warning (app is not code-signed)

**Bypassing Windows SmartScreen:**
1. Click "More info" on the warning dialog
2. Click "Run anyway"
3. The app will launch normally after this

### Linux

1. Download `mysql-to-sheets-X.X.X-x86_64.AppImage`
2. Make it executable: `chmod +x mysql-to-sheets-*.AppImage`
3. Run it: `./mysql-to-sheets-*.AppImage`

No installation needed — AppImage is a portable format.

### Auto-Updates

The desktop app checks for updates automatically once per day. You can also check manually via the system tray menu: **Check for Updates...**

When an update is available, you'll see a notification and a menu item to download it.

## Google Cloud Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Google Sheets API** (APIs & Services > Library)
3. Create a **Service Account** (APIs & Services > Credentials > Create Credentials)
4. Download the JSON key and save as `service_account.json`
5. Find the `client_email` in the JSON file
6. **Share** your Google Sheet with that email as **Editor**

For detailed instructions, common mistakes, and troubleshooting, see the [Google Cloud Setup Guide](docs/google-cloud-setup.md).

## Security Notes

- Never commit `.env` or `service_account.json` to version control (already in `.gitignore`)
- Create a database user with SELECT-only permissions for sync operations
- SQL validation is enabled by default (blocks DROP, DELETE, etc.)
- API authentication is enabled by default
- Account lockout after 5 failed login attempts
- RBAC uses fail-closed design — unknown permissions are denied
- Webhook deliveries are signed with HMAC-SHA256

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "Spreadsheet not found" | Sheet ID incorrect or not shared | Verify ID and share with service account email |
| "Connection refused" | Database not accessible | Check host, port, firewall rules |
| "Service account file not found" | Missing credentials | Download JSON from Google Cloud Console |
| "Worksheet not found" | Tab name mismatch | Check `GOOGLE_WORKSHEET_NAME` |
| "UnsupportedDatabaseError" | Invalid `DB_TYPE` | Use `mysql`, `postgres`, `sqlite`, or `mssql` |
| "ModuleNotFoundError: psycopg2" | PostgreSQL driver missing | `pip install mysql-to-sheets[postgres]` |

Run full diagnostics:

```bash
python -m mysql_to_sheets diagnose
```

## Roadmap

- [PRIORITIES.md](PRIORITIES.md) — Market-readiness priorities (ship blockers → growth)
- [ROADMAP.md](ROADMAP.md) — Completed development phases and future items
- [STANDALONE_PROJECTS.md](STANDALONE_PROJECTS.md) — Extractable packages and standalone services

## License

MIT
