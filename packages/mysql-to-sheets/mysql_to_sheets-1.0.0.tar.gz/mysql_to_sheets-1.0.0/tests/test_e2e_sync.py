"""End-to-end sync tests.

Tier A: SQLite demo DB → full sync pipeline → mocked gspread.
    Always runs. Validates the ETL pipeline end-to-end without external deps.

Tier B: Real database → real Google Sheets API.
    Requires SERVICE_ACCOUNT_FILE and E2E_GOOGLE_SHEET_ID env vars.
    Skips gracefully when credentials are unavailable.

Note: All tests in this module are marked as @pytest.mark.e2e.
Run with `pytest -m e2e` to run only these tests, or exclude with `pytest -m "not e2e"`.
"""

import os
import sqlite3
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Mark all tests in this module as e2e
pytestmark = pytest.mark.e2e

from mysql_to_sheets.core.config import Config, reset_config
from mysql_to_sheets.core.demo import SAMPLE_CUSTOMERS, SAMPLE_PRODUCTS
from mysql_to_sheets.core.sync import run_sync


def _has_real_credentials() -> bool:
    """Check if real Google Sheets credentials are available."""
    sa_file = os.environ.get("SERVICE_ACCOUNT_FILE", "")
    sheet_id = os.environ.get("E2E_GOOGLE_SHEET_ID", "")
    return bool(sa_file and os.path.exists(sa_file) and sheet_id)


requires_real_creds = pytest.mark.skipif(
    not _has_real_credentials(),
    reason="Real Google Sheets credentials not available (set SERVICE_ACCOUNT_FILE and E2E_GOOGLE_SHEET_ID)",
)


def _create_test_db(path: str) -> None:
    """Create a minimal SQLite test database."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE sample_customers "
        "(id INTEGER PRIMARY KEY, name TEXT, email TEXT, created_at TEXT, status TEXT)"
    )
    cur.executemany(
        "INSERT INTO sample_customers VALUES (?, ?, ?, ?, ?)",
        SAMPLE_CUSTOMERS,
    )
    cur.execute(
        "CREATE TABLE sample_products "
        "(id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL)"
    )
    cur.executemany(
        "INSERT INTO sample_products VALUES (?, ?, ?, ?)",
        SAMPLE_PRODUCTS,
    )
    conn.commit()
    conn.close()


@pytest.fixture()
def demo_db(tmp_path):
    """Create a temporary SQLite demo database and return its path."""
    db_path = str(tmp_path / "e2e_test.db")
    _create_test_db(db_path)
    return db_path


@pytest.fixture()
def demo_config(demo_db, tmp_path):
    """Config pointing to SQLite demo DB with mocked sheet ID."""
    # Create a fake service account file so validation passes
    # Must include all required fields: type, client_email, private_key
    fake_sa = tmp_path / "fake_sa.json"
    fake_sa.write_text(
        '{"type": "service_account", '
        '"client_email": "test@test.iam.gserviceaccount.com", '
        '"private_key": "-----BEGIN RSA PRIVATE KEY-----\\nfake\\n-----END RSA PRIVATE KEY-----"}'
    )

    reset_config()
    config = Config(
        db_type="sqlite",
        db_host="",
        db_port=0,
        db_user="sqlite",
        db_password="unused",
        db_name=demo_db,
        google_sheet_id="test_e2e_sheet_id",
        google_worksheet_name="Sheet1",
        service_account_file=str(fake_sa),
        sql_query="SELECT * FROM sample_customers ORDER BY id",
        sql_validation_enabled=False,
        sync_mode="replace",
    )
    yield config
    reset_config()


@pytest.fixture()
def mock_sheets():
    """Mock gspread at the service_account level.

    Returns a dict with gc, spreadsheet, worksheet mocks and a
    `get_pushed_data()` helper that returns all data written to the sheet.
    """
    mock_gc = MagicMock()
    mock_spreadsheet = MagicMock()
    mock_spreadsheet.title = "E2E Test Sheet"
    mock_worksheet = MagicMock()

    mock_gc.open_by_key.return_value = mock_spreadsheet
    mock_spreadsheet.worksheet.return_value = mock_worksheet
    mock_worksheet.get_all_values.return_value = []
    # Set up row_values to return expected headers for append mode validation
    mock_worksheet.row_values.return_value = ["id", "name", "email", "created_at", "status"]

    # Track data pushed via update() and append_rows()
    pushed_calls = []

    def _capture_update(*args, **kwargs):
        # update() is called with values= keyword arg
        data = kwargs.get("values") or (args[0] if args else [])
        pushed_calls.append(data)

    def _capture_append(*args, **kwargs):
        data = kwargs.get("values") or (args[0] if args else [])
        pushed_calls.append(data)

    mock_worksheet.update.side_effect = _capture_update
    mock_worksheet.append_rows.side_effect = _capture_append

    with patch("gspread.service_account", return_value=mock_gc):
        # Also patch the sheets_utils import used by push_to_sheets
        with patch(
            "mysql_to_sheets.core.sheets_utils.get_or_create_worksheet",
            return_value=mock_worksheet,
        ):
            with patch(
                "mysql_to_sheets.core.sheets_utils.parse_worksheet_identifier",
                return_value="Sheet1",
            ):
                yield {
                    "gc": mock_gc,
                    "spreadsheet": mock_spreadsheet,
                    "worksheet": mock_worksheet,
                    "pushed_calls": pushed_calls,
                }


# ---------------------------------------------------------------------------
# Tier A: SQLite + mocked gspread (always runs)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestE2EReplaceMode:
    """E2E test for replace sync mode."""

    def test_e2e_replace_mode(self, demo_config, mock_sheets):
        """Full pipeline: SQLite → fetch → clean → push (replace)."""
        result = run_sync(
            config=demo_config,
            dry_run=False,
            mode="replace",
            notify=False,
            skip_snapshot=True,
        )

        assert result.success is True
        assert result.rows_synced == len(SAMPLE_CUSTOMERS)
        assert len(result.headers) == 5  # id, name, email, created_at, status

        # Verify sheet was cleared then updated
        mock_sheets["worksheet"].clear.assert_called_once()
        assert len(mock_sheets["pushed_calls"]) == 1

        # First row should be headers + data
        pushed = mock_sheets["pushed_calls"][0]
        assert pushed[0] == ["id", "name", "email", "created_at", "status"]
        assert len(pushed) == len(SAMPLE_CUSTOMERS) + 1  # headers + rows


@pytest.mark.e2e
class TestE2EAppendMode:
    """E2E test for append sync mode."""

    def test_e2e_append_mode(self, demo_config, mock_sheets):
        """Full pipeline: SQLite → fetch → clean → push (append)."""
        result = run_sync(
            config=demo_config,
            dry_run=False,
            mode="append",
            notify=False,
            skip_snapshot=True,
        )

        assert result.success is True
        assert result.rows_synced == len(SAMPLE_CUSTOMERS)

        # Append mode should NOT clear the sheet
        mock_sheets["worksheet"].clear.assert_not_called()


@pytest.mark.e2e
class TestE2EStreamingMode:
    """E2E test for streaming sync mode.

    Note: Streaming mode uses mysql.connector directly and does not support
    SQLite. This test requires a real MySQL database and is Tier B only.
    """

    @requires_real_creds
    def test_e2e_streaming_mode(self, demo_config, mock_sheets):
        """Full pipeline: MySQL → streaming sync with small chunks.

        Skipped when real credentials are unavailable because streaming
        mode hardcodes MySQL connector and cannot use SQLite.
        """
        result = run_sync(
            config=demo_config,
            dry_run=False,
            mode="streaming",
            chunk_size=5,
            notify=False,
            skip_snapshot=True,
        )

        assert result.success is True
        assert result.rows_synced == len(SAMPLE_CUSTOMERS)
        assert "chunks" in result.message.lower()


@pytest.mark.e2e
class TestE2EPreviewMode:
    """E2E test for preview mode (diff without pushing)."""

    def test_e2e_preview_mode(self, demo_config, mock_sheets):
        """Preview should return diff without pushing data."""
        result = run_sync(
            config=demo_config,
            preview=True,
            notify=False,
            skip_snapshot=True,
        )

        assert result.success is True
        assert result.preview is True
        assert result.diff is not None

        # Sheet should NOT be updated in preview mode
        mock_sheets["worksheet"].update.assert_not_called()
        mock_sheets["worksheet"].clear.assert_not_called()


@pytest.mark.e2e
class TestE2EDryRun:
    """E2E test for dry run mode."""

    def test_e2e_dry_run(self, demo_config, mock_sheets):
        """Dry run should validate without pushing."""
        result = run_sync(
            config=demo_config,
            dry_run=True,
            notify=False,
            skip_snapshot=True,
        )

        assert result.success is True
        assert result.rows_synced == len(SAMPLE_CUSTOMERS)
        assert "dry run" in result.message.lower()

        # Nothing should be pushed
        mock_sheets["worksheet"].update.assert_not_called()
        mock_sheets["worksheet"].clear.assert_not_called()


@pytest.mark.e2e
class TestE2EColumnMapping:
    """E2E test for column mapping."""

    def test_e2e_column_mapping(self, demo_config, mock_sheets):
        """Column mapping should rename and reorder columns."""
        from mysql_to_sheets.core.column_mapping import ColumnMappingConfig

        col_config = ColumnMappingConfig(
            enabled=True,
            rename_map={"name": "Customer Name", "email": "Email Address"},
            column_order=["Customer Name", "Email Address", "status"],
        )

        result = run_sync(
            config=demo_config,
            dry_run=False,
            mode="replace",
            column_mapping_config=col_config,
            notify=False,
            skip_snapshot=True,
        )

        assert result.success is True
        assert "Customer Name" in result.headers
        assert "Email Address" in result.headers
        assert len(result.headers) == 3  # Only the 3 specified columns


@pytest.mark.e2e
class TestE2EProductsQuery:
    """E2E test with a different query to verify query flexibility."""

    def test_e2e_products_query(self, demo_config, mock_sheets):
        """Sync products table instead of customers."""
        demo_config.sql_query = "SELECT * FROM sample_products ORDER BY id"

        result = run_sync(
            config=demo_config,
            dry_run=False,
            mode="replace",
            notify=False,
            skip_snapshot=True,
        )

        assert result.success is True
        assert result.rows_synced == len(SAMPLE_PRODUCTS)
        assert "name" in result.headers
        assert "category" in result.headers
        assert "price" in result.headers


# ---------------------------------------------------------------------------
# Tier B: Real credentials (skips if unavailable)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@requires_real_creds
class TestE2ERealSheets:
    """E2E tests using real Google Sheets API.

    Requires:
        - SERVICE_ACCOUNT_FILE env var pointing to a valid service account JSON
        - E2E_GOOGLE_SHEET_ID env var with a test spreadsheet ID
        - The spreadsheet must be shared with the service account email
    """

    @pytest.fixture()
    def real_config(self, demo_db):
        """Config with real Sheets credentials and SQLite demo DB."""
        reset_config()
        config = Config(
            db_type="sqlite",
            db_host="",
            db_port=0,
            db_user="",
            db_password="",
            db_name=demo_db,
            google_sheet_id=os.environ["E2E_GOOGLE_SHEET_ID"],
            google_worksheet_name="E2ETest",
            service_account_file=os.environ["SERVICE_ACCOUNT_FILE"],
            sql_query="SELECT * FROM sample_customers ORDER BY id",
            sql_validation_enabled=False,
            sync_mode="replace",
            worksheet_auto_create=True,
        )
        yield config
        reset_config()

    def test_e2e_real_sheets_replace(self, real_config):
        """Real sync: SQLite → Google Sheets (replace mode)."""
        result = run_sync(
            config=real_config,
            dry_run=False,
            mode="replace",
            notify=False,
            skip_snapshot=True,
            create_worksheet=True,
        )

        assert result.success is True
        assert result.rows_synced == len(SAMPLE_CUSTOMERS)

    def test_e2e_real_sheets_append(self, real_config):
        """Real sync: SQLite → Google Sheets (append mode)."""
        # First do a replace to start clean
        run_sync(
            config=real_config,
            dry_run=False,
            mode="replace",
            notify=False,
            skip_snapshot=True,
            create_worksheet=True,
        )

        # Then append
        result = run_sync(
            config=real_config,
            dry_run=False,
            mode="append",
            notify=False,
            skip_snapshot=True,
        )

        assert result.success is True
        assert result.rows_synced == len(SAMPLE_CUSTOMERS)

    def test_e2e_real_sheets_streaming(self, real_config):
        """Real sync: SQLite → Google Sheets (streaming mode)."""
        result = run_sync(
            config=real_config,
            dry_run=False,
            mode="streaming",
            chunk_size=5,
            notify=False,
            skip_snapshot=True,
            create_worksheet=True,
        )

        assert result.success is True
        assert result.rows_synced == len(SAMPLE_CUSTOMERS)
