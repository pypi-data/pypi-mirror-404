# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **PostgreSQL connection pooling** — reuses `DB_POOL_ENABLED` / `DB_POOL_SIZE` env vars, uses `psycopg2.pool.ThreadedConnectionPool`
- **Python 3.13 support** — added to CI matrix and PyPI classifiers

### Changed

- **Rate limiting enabled by default** — `RATE_LIMIT_ENABLED` now defaults to `true` (60 req/min). Set `RATE_LIMIT_ENABLED=false` to disable.

## [1.0.0] - 2026-01-27

### Added

- **Multi-database support** — MySQL, PostgreSQL, SQLite, and SQL Server
- **Three sync modes** — full replace, append, and streaming (chunked processing for large datasets)
- **CLI interface** with 22 command modules: sync, validate, quickstart, schedule, snapshot, rollback, and more
- **REST API** (FastAPI) with OpenAPI docs, authentication, rate limiting, and CORS
- **Web Dashboard** (Flask) with sync controls, history, diagnostics, and configuration management
- **Desktop application** packaging via PyInstaller
- **Interactive setup wizard** (`quickstart` command) for first-time configuration
- **Demo mode** (`--demo`) to evaluate without a real database
- **Column mapping** — rename, reorder, filter, and transform column names
- **Preview and dry-run** — see diffs before applying changes
- **Snapshots and rollback** — save and restore previous sheet states
- **Incremental sync** — timestamp-based change detection
- **Retry with circuit breaker** — exponential backoff and automatic failure isolation
- **Job queue** with SQLite and Redis backends for async processing
- **Distributed workers** with heartbeat monitoring and job stealing
- **Freshness/SLA monitoring** — track data staleness with configurable alerts
- **Multi-tenant architecture** — organizations, users, RBAC (owner/admin/operator/viewer)
- **JWT authentication** with access/refresh tokens and account lockout
- **Webhook system** — subscribe to sync events with HMAC-SHA256 signed deliveries
- **Notifications** — email (SMTP), Slack, and webhook backends
- **Prometheus metrics** endpoint for monitoring
- **Subscription tiers** — FREE, PRO, BUSINESS, ENTERPRISE with usage metering
- **RS256 license keys** — offline-validated JWT license keys for paid tiers
- **Trial management** — automatic trial periods with expiration handling
- **Billing webhook receiver** — integration point for Stripe and other payment processors
- **Audit logging** with export and retention policies
- **Alembic database migrations** for schema management
- **Helm chart** for Kubernetes deployment
- **GitHub Actions CI/CD** with lint, type check, tests, security scan, and Docker build
- **Prometheus alerting rules** and Grafana dashboard templates

[1.0.0]: https://github.com/BrandonFricke/mysql-to-sheets/releases/tag/v1.0.0
