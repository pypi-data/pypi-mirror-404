"""Tests for CLI command handlers."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.cli.main import cli
from mysql_to_sheets.core.exceptions import SchedulerError
from mysql_to_sheets.core.sync import SyncResult


# Mock for tier checks - allows all features to pass
def mock_check_cli_tier_pass(feature):
    """Mock check_cli_tier that always allows access."""
    return (True, None)


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_scheduler.db"


@patch("mysql_to_sheets.cli.tier_check.check_cli_tier", mock_check_cli_tier_pass)
class TestScheduleCommands:
    """Tests for schedule command handlers."""

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_add_with_cron(self, mock_get_service, capsys):
        """Test schedule add with cron expression."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "daily-sync"
        mock_job.schedule_display = "0 6 * * *"
        mock_job.sheet_id = None
        mock_job.to_dict.return_value = {
            "id": 1,
            "name": "daily-sync",
            "cron_expression": "0 6 * * *",
        }
        mock_service.add_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "add", "--name", "daily-sync", "--cron", "0 6 * * *"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Schedule created successfully" in captured.out
        assert "daily-sync" in captured.out

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_add_with_interval(self, mock_get_service, capsys):
        """Test schedule add with interval."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 2
        mock_job.name = "hourly-sync"
        mock_job.schedule_display = "Every 60 minutes"
        mock_job.sheet_id = None
        mock_job.to_dict.return_value = {
            "id": 2,
            "name": "hourly-sync",
            "interval_minutes": 60,
        }
        mock_service.add_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "add", "--name", "hourly-sync", "--interval", "60"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Schedule created successfully" in captured.out

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_add_json_output(self, mock_get_service, capsys):
        """Test schedule add with JSON output."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 3
        mock_job.name = "json-sync"
        mock_job.schedule_display = "0 * * * *"
        mock_job.to_dict.return_value = {
            "id": 3,
            "name": "json-sync",
            "cron_expression": "0 * * * *",
            "enabled": True,
        }
        mock_service.add_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        result = cli(
            ["schedule", "add", "--name", "json-sync", "--cron", "0 * * * *", "--output", "json"]
        )

        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is True
        assert output["schedule"]["name"] == "json-sync"

    def test_schedule_add_missing_schedule(self, capsys):
        """Test schedule add fails without cron or interval."""
        result = cli(["schedule", "add", "--name", "invalid-sync"])

        assert result == 1
        captured = capsys.readouterr()
        assert "cron" in captured.out.lower() or "interval" in captured.out.lower()

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_list(self, mock_get_service, capsys):
        """Test schedule list command."""
        mock_service = MagicMock()
        mock_job1 = MagicMock()
        mock_job1.id = 1
        mock_job1.name = "job1"
        mock_job1.schedule_display = "0 6 * * *"
        mock_job1.status = MagicMock(value="pending")
        mock_job1.last_run_at = None
        mock_job1.to_dict.return_value = {"id": 1, "name": "job1"}

        mock_job2 = MagicMock()
        mock_job2.id = 2
        mock_job2.name = "job2"
        mock_job2.schedule_display = "0 12 * * *"
        mock_job2.status = MagicMock(value="running")
        mock_job2.last_run_at = datetime.now(timezone.utc)
        mock_job2.to_dict.return_value = {"id": 2, "name": "job2"}

        mock_service.get_all_jobs.return_value = [mock_job1, mock_job2]
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "list"])

        assert result == 0
        captured = capsys.readouterr()
        assert "2 found" in captured.out
        assert "job1" in captured.out
        assert "job2" in captured.out

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_list_empty(self, mock_get_service, capsys):
        """Test schedule list with no jobs."""
        mock_service = MagicMock()
        mock_service.get_all_jobs.return_value = []
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "list"])

        assert result == 0
        captured = capsys.readouterr()
        assert "No scheduled jobs found" in captured.out

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_list_json_output(self, mock_get_service, capsys):
        """Test schedule list with JSON output."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "test-job"
        mock_job.to_dict.return_value = {"id": 1, "name": "test-job", "enabled": True}
        mock_service.get_all_jobs.return_value = [mock_job]
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "list", "--output", "json"])

        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is True
        assert output["total"] == 1
        assert isinstance(output["schedules"], list)

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_remove_success(self, mock_get_service, capsys):
        """Test schedule remove success."""
        mock_service = MagicMock()
        mock_service.delete_job.return_value = True
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "remove", "--id", "1"])

        assert result == 0
        captured = capsys.readouterr()
        assert "removed" in captured.out.lower()

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_remove_not_found(self, mock_get_service, capsys):
        """Test schedule remove not found."""
        mock_service = MagicMock()
        mock_service.delete_job.return_value = False
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "remove", "--id", "999"])

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_enable(self, mock_get_service, capsys):
        """Test schedule enable command."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.name = "enabled-job"
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "enable", "--id", "1"])

        assert result == 0
        mock_service.enable_job.assert_called_once_with(1)
        captured = capsys.readouterr()
        assert "enabled" in captured.out.lower()

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_enable_not_found(self, mock_get_service, capsys):
        """Test schedule enable for non-existent job."""
        mock_service = MagicMock()
        mock_service.enable_job.side_effect = SchedulerError("Job not found")
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "enable", "--id", "999"])

        assert result == 1

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_disable(self, mock_get_service, capsys):
        """Test schedule disable command."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.name = "disabled-job"
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "disable", "--id", "1"])

        assert result == 0
        mock_service.disable_job.assert_called_once_with(1)
        captured = capsys.readouterr()
        assert "disabled" in captured.out.lower()

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_trigger_success(self, mock_get_service, capsys):
        """Test schedule trigger success."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.name = "triggered-job"
        mock_job.last_run_success = True
        mock_job.last_run_rows = 50
        mock_job.last_run_message = "Sync completed"
        mock_job.to_dict.return_value = {
            "id": 1,
            "name": "triggered-job",
            "last_run_success": True,
        }
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "trigger", "--id", "1"])

        assert result == 0
        mock_service.trigger_job.assert_called_once_with(1)
        captured = capsys.readouterr()
        assert "triggered" in captured.out.lower()

    @patch("mysql_to_sheets.cli.schedule_commands.get_scheduler_service")
    def test_schedule_trigger_not_found(self, mock_get_service, capsys):
        """Test schedule trigger for non-existent job."""
        mock_service = MagicMock()
        mock_service.get_job.return_value = None
        mock_get_service.return_value = mock_service

        result = cli(["schedule", "trigger", "--id", "999"])

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()


class TestAPIKeyCommands:
    """Tests for api-key command handlers."""

    @patch("mysql_to_sheets.cli.api_key_commands.get_api_key_repository")
    @patch("mysql_to_sheets.cli.api_key_commands.get_config")
    def test_api_key_create(self, mock_get_config, mock_get_repo, capsys):
        """Test api-key create command."""
        mock_config = MagicMock()
        mock_config.history_db_path = "/tmp/test.db"
        mock_get_config.return_value = mock_config

        mock_repo = MagicMock()
        mock_key = MagicMock()
        mock_key.id = 1
        mock_key.name = "test-key"
        mock_key.key_prefix = "mts_abc1"
        mock_key.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_repo.create.return_value = mock_key
        mock_get_repo.return_value = mock_repo

        result = cli(["api-key", "create", "--name", "test-key"])

        assert result == 0
        captured = capsys.readouterr()
        assert "test-key" in captured.out
        mock_repo.create.assert_called_once()

    @patch("mysql_to_sheets.cli.api_key_commands.get_api_key_repository")
    @patch("mysql_to_sheets.cli.api_key_commands.get_config")
    def test_api_key_create_json_output(self, mock_get_config, mock_get_repo, capsys):
        """Test api-key create with JSON output."""
        mock_config = MagicMock()
        mock_config.history_db_path = "/tmp/test.db"
        mock_get_config.return_value = mock_config

        mock_repo = MagicMock()
        mock_key = MagicMock()
        mock_key.id = 1
        mock_key.name = "json-key"
        mock_key.key_prefix = "mts_json"
        mock_key.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_repo.create.return_value = mock_key
        mock_get_repo.return_value = mock_repo

        result = cli(["api-key", "create", "--name", "json-key", "--output", "json"])

        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is True
        assert output["api_key"]["name"] == "json-key"

    @patch("mysql_to_sheets.cli.api_key_commands.get_api_key_repository")
    @patch("mysql_to_sheets.cli.api_key_commands.get_config")
    def test_api_key_list(self, mock_get_config, mock_get_repo, capsys):
        """Test api-key list command."""
        mock_config = MagicMock()
        mock_config.history_db_path = "/tmp/test.db"
        mock_get_config.return_value = mock_config

        mock_repo = MagicMock()
        mock_key = MagicMock()
        mock_key.id = 1
        mock_key.name = "prod-key"
        mock_key.key_prefix = "mts_prod"
        mock_key.is_active = True
        mock_key.last_used_at = None
        mock_repo.get_all.return_value = [mock_key]
        mock_get_repo.return_value = mock_repo

        result = cli(["api-key", "list"])

        assert result == 0
        captured = capsys.readouterr()
        assert "prod-key" in captured.out

    @patch("mysql_to_sheets.cli.api_key_commands.get_api_key_repository")
    @patch("mysql_to_sheets.cli.api_key_commands.get_config")
    def test_api_key_list_empty(self, mock_get_config, mock_get_repo, capsys):
        """Test api-key list with no keys."""
        mock_config = MagicMock()
        mock_config.history_db_path = "/tmp/test.db"
        mock_get_config.return_value = mock_config

        mock_repo = MagicMock()
        mock_repo.get_all.return_value = []
        mock_get_repo.return_value = mock_repo

        result = cli(["api-key", "list"])

        assert result == 0
        captured = capsys.readouterr()
        assert "No API keys found" in captured.out

    @patch("mysql_to_sheets.cli.api_key_commands.get_api_key_repository")
    @patch("mysql_to_sheets.cli.api_key_commands.get_config")
    def test_api_key_list_json_output(self, mock_get_config, mock_get_repo, capsys):
        """Test api-key list with JSON output."""
        mock_config = MagicMock()
        mock_config.history_db_path = "/tmp/test.db"
        mock_get_config.return_value = mock_config

        mock_repo = MagicMock()
        mock_key = MagicMock()
        mock_key.id = 1
        mock_key.name = "json-list-key"
        mock_key.description = "Test"
        mock_key.key_prefix = "mts_json"
        mock_key.is_active = True
        mock_key.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_key.last_used_at = None
        mock_repo.get_all.return_value = [mock_key]
        mock_get_repo.return_value = mock_repo

        result = cli(["api-key", "list", "--output", "json"])

        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is True
        assert output["total"] == 1

    @patch("mysql_to_sheets.cli.api_key_commands.get_api_key_repository")
    @patch("mysql_to_sheets.cli.api_key_commands.get_config")
    def test_api_key_revoke_success(self, mock_get_config, mock_get_repo, capsys):
        """Test api-key revoke success."""
        mock_config = MagicMock()
        mock_config.history_db_path = "/tmp/test.db"
        mock_get_config.return_value = mock_config

        mock_repo = MagicMock()
        mock_key = MagicMock()
        mock_key.name = "revoke-key"
        mock_key.is_active = True
        mock_repo.get_by_id.return_value = mock_key
        mock_get_repo.return_value = mock_repo

        result = cli(["api-key", "revoke", "--id", "1"])

        assert result == 0
        mock_repo.revoke.assert_called_once_with(1)

    @patch("mysql_to_sheets.cli.api_key_commands.get_api_key_repository")
    @patch("mysql_to_sheets.cli.api_key_commands.get_config")
    def test_api_key_revoke_not_found(self, mock_get_config, mock_get_repo, capsys):
        """Test api-key revoke not found."""
        mock_config = MagicMock()
        mock_config.history_db_path = "/tmp/test.db"
        mock_get_config.return_value = mock_config

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None
        mock_get_repo.return_value = mock_repo

        result = cli(["api-key", "revoke", "--id", "999"])

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    @patch("mysql_to_sheets.cli.api_key_commands.get_api_key_repository")
    @patch("mysql_to_sheets.cli.api_key_commands.get_config")
    def test_api_key_revoke_already_revoked(self, mock_get_config, mock_get_repo, capsys):
        """Test api-key revoke for already revoked key."""
        mock_config = MagicMock()
        mock_config.history_db_path = "/tmp/test.db"
        mock_get_config.return_value = mock_config

        mock_repo = MagicMock()
        mock_key = MagicMock()
        mock_key.name = "old-key"
        mock_key.is_active = False
        mock_repo.get_by_id.return_value = mock_key
        mock_get_repo.return_value = mock_repo

        result = cli(["api-key", "revoke", "--id", "1"])

        assert result == 1
        captured = capsys.readouterr()
        assert "already revoked" in captured.out.lower()


@patch("mysql_to_sheets.cli.tier_check.check_cli_tier", mock_check_cli_tier_pass)
class TestSyncCommands:
    """Tests for sync command variations."""

    @patch("mysql_to_sheets.cli.sync_commands.setup_logging")
    @patch("mysql_to_sheets.cli.sync_commands.run_sync")
    @patch("mysql_to_sheets.cli.sync_commands.get_config")
    @patch("mysql_to_sheets.cli.sync_commands.reset_config")
    def test_sync_dry_run(
        self, mock_reset, mock_get_config, mock_run_sync, mock_setup_logging, capsys
    ):
        """Test sync --dry-run flag."""
        mock_config = MagicMock()
        mock_config.with_overrides.return_value = mock_config
        mock_config.validate.return_value = []
        mock_config.notify_on_success = False
        mock_config.notify_on_failure = False
        mock_config.license_key = ""  # No license - skip license check
        mock_get_config.return_value = mock_config

        mock_run_sync.return_value = SyncResult(
            success=True,
            rows_synced=100,
            columns=5,
            headers=["a", "b", "c", "d", "e"],
            message="Dry run: would sync 100 rows",
        )

        result = cli(["sync", "--dry-run"])

        assert result == 0
        # Verify dry_run was passed
        mock_run_sync.assert_called_once()
        call_kwargs = mock_run_sync.call_args
        assert call_kwargs[1].get("dry_run") is True or (
            len(call_kwargs[0]) > 1 and call_kwargs[0][1] is True
        )

    @patch("mysql_to_sheets.cli.sync_commands.setup_logging")
    @patch("mysql_to_sheets.cli.sync_commands.run_sync")
    @patch("mysql_to_sheets.cli.sync_commands.get_config")
    @patch("mysql_to_sheets.cli.sync_commands.reset_config")
    def test_sync_json_output(
        self, mock_reset, mock_get_config, mock_run_sync, mock_setup_logging, capsys
    ):
        """Test sync --output json flag."""
        mock_config = MagicMock()
        mock_config.with_overrides.return_value = mock_config
        mock_config.validate.return_value = []
        mock_config.notify_on_success = False
        mock_config.notify_on_failure = False
        mock_config.license_key = ""  # No license - skip license check
        mock_get_config.return_value = mock_config

        mock_run_sync.return_value = SyncResult(
            success=True,
            rows_synced=50,
            columns=3,
            headers=["id", "name", "value"],
            message="Sync completed",
        )

        result = cli(["sync", "--output", "json"])

        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is True
        assert output["rows_synced"] == 50


@patch("mysql_to_sheets.cli.tier_check.check_cli_tier", mock_check_cli_tier_pass)
class TestCliHelp:
    """Tests for CLI help and version."""

    def test_no_command_shows_help(self):
        """Test CLI with no command returns 0."""
        result = cli([])
        assert result == 0

    def test_help_flag(self):
        """Test --help flag exits cleanly."""
        with pytest.raises(SystemExit) as exc_info:
            cli(["--help"])
        assert exc_info.value.code == 0

    def test_version_flag(self):
        """Test --version flag exits cleanly."""
        with pytest.raises(SystemExit) as exc_info:
            cli(["--version"])
        assert exc_info.value.code == 0

    def test_schedule_no_subcommand(self, capsys):
        """Test schedule with no subcommand shows error."""
        result = cli(["schedule"])
        assert result == 1
        captured = capsys.readouterr()
        assert "No schedule command specified" in captured.out

    @patch("mysql_to_sheets.cli.api_key_commands.get_api_key_repository")
    @patch("mysql_to_sheets.cli.api_key_commands.get_config")
    def test_api_key_no_subcommand(self, mock_get_config, mock_get_repo, capsys):
        """Test api-key with no subcommand shows error."""
        mock_config = MagicMock()
        mock_config.history_db_path = "/tmp/test.db"
        mock_get_config.return_value = mock_config
        mock_get_repo.return_value = MagicMock()

        result = cli(["api-key"])
        assert result == 1
        captured = capsys.readouterr()
        assert "No api-key command specified" in captured.out
