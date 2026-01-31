"""Tests for the webhooks module."""

import os
import tempfile
from datetime import datetime, timezone

import pytest

from mysql_to_sheets.core.webhooks.payload import (
    WebhookPayload,
    create_config_payload,
    create_schedule_payload,
    create_sync_payload,
    create_test_payload,
    create_user_payload,
    generate_delivery_id,
)
from mysql_to_sheets.models.organizations import (
    Organization,
    OrganizationRepository,
    reset_organization_repository,
)
from mysql_to_sheets.models.webhooks import (
    VALID_EVENT_TYPES,
    WebhookDelivery,
    WebhookEventType,
    WebhookRepository,
    WebhookSubscription,
    get_webhook_repository,
    reset_webhook_repository,
)


class TestWebhookEventType:
    """Tests for WebhookEventType enum."""

    def test_sync_events(self):
        """Test sync event types."""
        assert WebhookEventType.SYNC_STARTED.value == "sync.started"
        assert WebhookEventType.SYNC_COMPLETED.value == "sync.completed"
        assert WebhookEventType.SYNC_FAILED.value == "sync.failed"

    def test_config_events(self):
        """Test config event types."""
        assert WebhookEventType.CONFIG_CREATED.value == "config.created"
        assert WebhookEventType.CONFIG_UPDATED.value == "config.updated"
        assert WebhookEventType.CONFIG_DELETED.value == "config.deleted"

    def test_schedule_events(self):
        """Test schedule event types."""
        assert WebhookEventType.SCHEDULE_TRIGGERED.value == "schedule.triggered"

    def test_valid_event_types_list(self):
        """Test VALID_EVENT_TYPES contains all enum values."""
        for event_type in WebhookEventType:
            assert event_type.value in VALID_EVENT_TYPES


class TestWebhookSubscription:
    """Tests for WebhookSubscription dataclass."""

    def test_create_subscription(self):
        """Test creating a webhook subscription."""
        sub = WebhookSubscription(
            name="Test Webhook",
            url="https://example.com/webhook",
            secret="secret123",
            events=["sync.completed", "sync.failed"],
            organization_id=1,
        )

        assert sub.name == "Test Webhook"
        assert sub.url == "https://example.com/webhook"
        assert sub.secret == "secret123"
        assert len(sub.events) == 2
        assert sub.is_active is True
        assert sub.retry_count == 3
        assert sub.failure_count == 0

    def test_to_dict_without_secret(self):
        """Test to_dict excludes secret by default."""
        sub = WebhookSubscription(
            name="Test",
            url="https://example.com",
            secret="hidden-secret",
            events=["sync.completed"],
            organization_id=1,
        )

        d = sub.to_dict()

        assert "secret" not in d
        assert d["name"] == "Test"
        assert d["url"] == "https://example.com"

    def test_to_dict_with_secret(self):
        """Test to_dict includes secret when requested."""
        sub = WebhookSubscription(
            name="Test",
            url="https://example.com",
            secret="visible-secret",
            events=["sync.completed"],
            organization_id=1,
        )

        d = sub.to_dict(include_secret=True)

        assert d["secret"] == "visible-secret"

    def test_from_dict(self):
        """Test creating subscription from dictionary."""
        data = {
            "id": 1,
            "name": "From Dict",
            "url": "https://hook.example.com",
            "secret": "s3cr3t",
            "events": ["sync.completed"],
            "organization_id": 1,
            "is_active": True,
        }

        sub = WebhookSubscription.from_dict(data)

        assert sub.id == 1
        assert sub.name == "From Dict"
        assert sub.url == "https://hook.example.com"

    def test_validate_valid(self):
        """Test validation of valid subscription."""
        sub = WebhookSubscription(
            name="Valid",
            url="https://example.com/hook",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )

        errors = sub.validate()
        assert len(errors) == 0

    def test_validate_missing_name(self):
        """Test validation catches missing name."""
        sub = WebhookSubscription(
            name="",
            url="https://example.com",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )

        errors = sub.validate()
        assert any("Name" in e for e in errors)

    def test_validate_missing_url(self):
        """Test validation catches missing URL."""
        sub = WebhookSubscription(
            name="Test",
            url="",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )

        errors = sub.validate()
        assert any("URL" in e for e in errors)

    def test_validate_invalid_url(self):
        """Test validation catches invalid URL."""
        sub = WebhookSubscription(
            name="Test",
            url="not-a-url",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )

        errors = sub.validate()
        assert any("http" in e.lower() for e in errors)

    def test_validate_no_events(self):
        """Test validation catches empty events list."""
        sub = WebhookSubscription(
            name="Test",
            url="https://example.com",
            secret="secret",
            events=[],
            organization_id=1,
        )

        errors = sub.validate()
        assert any("event" in e.lower() for e in errors)

    def test_validate_invalid_event(self):
        """Test validation catches invalid event type."""
        sub = WebhookSubscription(
            name="Test",
            url="https://example.com",
            secret="secret",
            events=["invalid.event"],
            organization_id=1,
        )

        errors = sub.validate()
        assert any("Invalid event" in e for e in errors)

    def test_validate_retry_count_bounds(self):
        """Test validation catches out-of-bounds retry count."""
        sub = WebhookSubscription(
            name="Test",
            url="https://example.com",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
            retry_count=15,  # Max is 10
        )

        errors = sub.validate()
        assert any("retry_count" in e for e in errors)


class TestWebhookDelivery:
    """Tests for WebhookDelivery dataclass."""

    def test_create_delivery(self):
        """Test creating a webhook delivery record."""
        delivery = WebhookDelivery(
            subscription_id=1,
            delivery_id="dlv_abc123",
            event="sync.completed",
            payload={"key": "value"},
        )

        assert delivery.subscription_id == 1
        assert delivery.delivery_id == "dlv_abc123"
        assert delivery.status == "pending"
        assert delivery.attempt_count == 1

    def test_to_dict(self):
        """Test converting delivery to dictionary."""
        delivery = WebhookDelivery(
            subscription_id=1,
            delivery_id="dlv_xyz",
            event="sync.failed",
            payload={"error": "Test error"},
            status="success",
            response_code=200,
        )

        d = delivery.to_dict()

        assert d["subscription_id"] == 1
        assert d["delivery_id"] == "dlv_xyz"
        assert d["status"] == "success"
        assert d["response_code"] == 200


class TestWebhookPayload:
    """Tests for WebhookPayload dataclass."""

    def test_create_payload(self):
        """Test creating a webhook payload."""
        payload = WebhookPayload(
            event="sync.completed",
            timestamp="2024-01-15T10:00:00Z",
            delivery_id="dlv_test",
            data={"rows_synced": 100},
        )

        assert payload.event == "sync.completed"
        assert payload.delivery_id == "dlv_test"
        assert payload.data["rows_synced"] == 100

    def test_to_dict(self):
        """Test converting payload to dictionary."""
        payload = WebhookPayload(
            event="test",
            timestamp="2024-01-01T00:00:00Z",
            delivery_id="dlv_123",
            data={"test": True},
        )

        d = payload.to_dict()

        assert d["event"] == "test"
        assert d["timestamp"] == "2024-01-01T00:00:00Z"
        assert d["delivery_id"] == "dlv_123"
        assert d["data"]["test"] is True

    def test_from_dict(self):
        """Test creating payload from dictionary."""
        data = {
            "event": "sync.started",
            "timestamp": "2024-01-15T12:00:00Z",
            "delivery_id": "dlv_from_dict",
            "data": {"config_name": "test"},
        }

        payload = WebhookPayload.from_dict(data)

        assert payload.event == "sync.started"
        assert payload.data["config_name"] == "test"


class TestGenerateDeliveryId:
    """Tests for generate_delivery_id function."""

    def test_format(self):
        """Test delivery ID format."""
        delivery_id = generate_delivery_id()

        assert delivery_id.startswith("dlv_")
        assert len(delivery_id) > 4

    def test_uniqueness(self):
        """Test that generated IDs are unique."""
        ids = [generate_delivery_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestCreateSyncPayload:
    """Tests for create_sync_payload function."""

    def test_create_completed_payload(self):
        """Test creating sync completed payload."""
        payload = create_sync_payload(
            event="sync.completed",
            sync_id="sync_123",
            config_name="daily-sync",
            rows_synced=500,
            duration_seconds=12.5,
            sheet_id="sheet_abc",
        )

        assert payload.event == "sync.completed"
        assert payload.data["sync_id"] == "sync_123"
        assert payload.data["rows_synced"] == 500
        assert payload.data["duration_seconds"] == 12.5
        assert payload.delivery_id.startswith("dlv_")

    def test_create_failed_payload(self):
        """Test creating sync failed payload."""
        payload = create_sync_payload(
            event="sync.failed",
            error_type="DatabaseError",
            error_message="Connection refused",
        )

        assert payload.event == "sync.failed"
        assert payload.data["error_type"] == "DatabaseError"
        assert payload.data["error_message"] == "Connection refused"

    def test_timestamp_is_iso_format(self):
        """Test that timestamp is in ISO format."""
        payload = create_sync_payload(event="sync.started")

        # Should be parseable as ISO timestamp
        datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))


class TestCreateConfigPayload:
    """Tests for create_config_payload function."""

    def test_create_config_created(self):
        """Test creating config created payload."""
        payload = create_config_payload(
            event="config.created",
            config_id=1,
            config_name="new-config",
            user_email="admin@example.com",
        )

        assert payload.event == "config.created"
        assert payload.data["config_id"] == 1
        assert payload.data["config_name"] == "new-config"

    def test_create_config_updated_with_changes(self):
        """Test creating config updated payload with changes."""
        changes = {"name": "updated-name", "sql_query": "SELECT 1"}

        payload = create_config_payload(
            event="config.updated",
            config_id=1,
            changes=changes,
        )

        assert payload.data["changes"] == changes


class TestCreateSchedulePayload:
    """Tests for create_schedule_payload function."""

    def test_create_schedule_triggered(self):
        """Test creating schedule triggered payload."""
        next_run = datetime(2024, 1, 16, 6, 0, 0, tzinfo=timezone.utc)

        payload = create_schedule_payload(
            event="schedule.triggered",
            job_id=1,
            job_name="daily-sync",
            schedule_type="cron",
            next_run=next_run,
        )

        assert payload.event == "schedule.triggered"
        assert payload.data["job_id"] == 1
        assert payload.data["schedule_type"] == "cron"
        assert "2024-01-16" in payload.data["next_run"]


class TestCreateUserPayload:
    """Tests for create_user_payload function."""

    def test_create_user_created(self):
        """Test creating user created payload."""
        payload = create_user_payload(
            event="user.created",
            user_id=1,
            user_email="new@example.com",
            role="operator",
            changed_by_email="admin@example.com",
        )

        assert payload.event == "user.created"
        assert payload.data["user_id"] == 1
        assert payload.data["role"] == "operator"


class TestCreateTestPayload:
    """Tests for create_test_payload function."""

    def test_create_test(self):
        """Test creating test payload."""
        payload = create_test_payload()

        assert payload.event == "webhook.test"
        assert payload.data["test"] is True
        assert "message" in payload.data


class TestWebhookRepository:
    """Tests for WebhookRepository."""

    def setup_method(self):
        """Reset singletons before each test."""
        reset_webhook_repository()
        reset_organization_repository()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_webhook_repository()
        reset_organization_repository()

    def _create_org(self, db_path: str) -> Organization:
        """Helper to create a test organization."""
        org_repo = OrganizationRepository(db_path)
        return org_repo.create(Organization(name="Test Org", slug="test-org"))

    def test_create_subscription(self):
        """Test creating a webhook subscription."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = WebhookRepository(db_path)

            sub = WebhookSubscription(
                name="New Hook",
                url="https://example.com/hook",
                secret="secret123",
                events=["sync.completed"],
                organization_id=org.id,
            )

            created = repo.create_subscription(sub)

            assert created.id is not None
            assert created.name == "New Hook"
            assert created.created_at is not None
        finally:
            os.unlink(db_path)

    def test_create_invalid_subscription_raises(self):
        """Test creating invalid subscription raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = WebhookRepository(db_path)

            sub = WebhookSubscription(
                name="",  # Invalid: empty name
                url="https://example.com",
                secret="secret",
                events=["sync.completed"],
                organization_id=org.id,
            )

            with pytest.raises(ValueError):
                repo.create_subscription(sub)
        finally:
            os.unlink(db_path)

    def test_get_subscription_by_id(self):
        """Test getting subscription by ID."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = WebhookRepository(db_path)

            sub = repo.create_subscription(
                WebhookSubscription(
                    name="Test",
                    url="https://example.com",
                    secret="secret",
                    events=["sync.completed"],
                    organization_id=org.id,
                )
            )

            found = repo.get_subscription_by_id(sub.id, org.id)

            assert found is not None
            assert found.name == "Test"
        finally:
            os.unlink(db_path)

    def test_get_subscriptions_for_event(self):
        """Test getting subscriptions for a specific event."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = WebhookRepository(db_path)

            # Create subscription for sync.completed
            repo.create_subscription(
                WebhookSubscription(
                    name="Sync Hook",
                    url="https://example.com/sync",
                    secret="secret1",
                    events=["sync.completed"],
                    organization_id=org.id,
                )
            )

            # Create subscription for config events only
            repo.create_subscription(
                WebhookSubscription(
                    name="Config Hook",
                    url="https://example.com/config",
                    secret="secret2",
                    events=["config.created", "config.updated"],
                    organization_id=org.id,
                )
            )

            # Get hooks for sync.completed
            hooks = repo.get_subscriptions_for_event("sync.completed", org.id)

            assert len(hooks) == 1
            assert hooks[0].name == "Sync Hook"
        finally:
            os.unlink(db_path)

    def test_get_all_subscriptions(self):
        """Test getting all subscriptions for organization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = WebhookRepository(db_path)

            for i in range(3):
                repo.create_subscription(
                    WebhookSubscription(
                        name=f"Hook {i}",
                        url=f"https://example.com/hook{i}",
                        secret="secret",
                        events=["sync.completed"],
                        organization_id=org.id,
                    )
                )

            subs = repo.get_all_subscriptions(org.id)
            assert len(subs) == 3
        finally:
            os.unlink(db_path)

    def test_update_subscription(self):
        """Test updating a subscription."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = WebhookRepository(db_path)

            sub = repo.create_subscription(
                WebhookSubscription(
                    name="Original",
                    url="https://example.com/original",
                    secret="secret",
                    events=["sync.completed"],
                    organization_id=org.id,
                )
            )

            sub.name = "Updated"
            sub.events = ["sync.completed", "sync.failed"]
            updated = repo.update_subscription(sub)

            assert updated.name == "Updated"
            assert len(updated.events) == 2
        finally:
            os.unlink(db_path)

    def test_delete_subscription(self):
        """Test deleting a subscription."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = WebhookRepository(db_path)

            sub = repo.create_subscription(
                WebhookSubscription(
                    name="To Delete",
                    url="https://example.com",
                    secret="secret",
                    events=["sync.completed"],
                    organization_id=org.id,
                )
            )

            deleted = repo.delete_subscription(sub.id, org.id)

            assert deleted is True
            assert repo.get_subscription_by_id(sub.id, org.id) is None
        finally:
            os.unlink(db_path)

    def test_update_subscription_triggered(self):
        """Test updating subscription after delivery."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = WebhookRepository(db_path)

            sub = repo.create_subscription(
                WebhookSubscription(
                    name="Trigger Test",
                    url="https://example.com",
                    secret="secret",
                    events=["sync.completed"],
                    organization_id=org.id,
                )
            )

            assert sub.last_triggered_at is None
            assert sub.failure_count == 0

            # Update as success
            repo.update_subscription_triggered(sub.id, success=True)

            found = repo.get_subscription_by_id(sub.id, org.id)
            assert found.last_triggered_at is not None
            assert found.failure_count == 0

            # Update as failure
            repo.update_subscription_triggered(sub.id, success=False)

            found = repo.get_subscription_by_id(sub.id, org.id)
            assert found.failure_count == 1
        finally:
            os.unlink(db_path)

    def test_create_and_get_delivery(self):
        """Test creating and retrieving delivery records."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = WebhookRepository(db_path)

            sub = repo.create_subscription(
                WebhookSubscription(
                    name="Delivery Test",
                    url="https://example.com",
                    secret="secret",
                    events=["sync.completed"],
                    organization_id=org.id,
                )
            )

            delivery = WebhookDelivery(
                subscription_id=sub.id,
                delivery_id="dlv_test123",
                event="sync.completed",
                payload={"test": True},
            )

            created = repo.create_delivery(delivery)

            assert created.id is not None
            assert created.created_at is not None

            # Get by delivery_id
            found = repo.get_delivery_by_id("dlv_test123")
            assert found is not None
            assert found.event == "sync.completed"
        finally:
            os.unlink(db_path)

    def test_get_deliveries_for_subscription(self):
        """Test getting delivery history for a subscription."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = WebhookRepository(db_path)

            sub = repo.create_subscription(
                WebhookSubscription(
                    name="History Test",
                    url="https://example.com",
                    secret="secret",
                    events=["sync.completed"],
                    organization_id=org.id,
                )
            )

            # Create multiple deliveries
            for i in range(5):
                repo.create_delivery(
                    WebhookDelivery(
                        subscription_id=sub.id,
                        delivery_id=f"dlv_{i}",
                        event="sync.completed",
                        payload={"index": i},
                        status="success" if i % 2 == 0 else "failed",
                    )
                )

            # Get all
            deliveries = repo.get_deliveries_for_subscription(sub.id)
            assert len(deliveries) == 5

            # Filter by status
            success_only = repo.get_deliveries_for_subscription(sub.id, status="success")
            assert len(success_only) == 3
        finally:
            os.unlink(db_path)


class TestWebhookSingleton:
    """Tests for the webhook repository singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_webhook_repository()
        reset_organization_repository()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_webhook_repository()
        reset_organization_repository()

    def test_get_webhook_repository_requires_path(self):
        """Test that first call requires db_path."""
        with pytest.raises(ValueError) as exc_info:
            get_webhook_repository()

        assert "db_path is required" in str(exc_info.value)

    def test_reset_webhook_repository(self):
        """Test resetting the singleton."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            get_webhook_repository(db_path)
            reset_webhook_repository()

            with pytest.raises(ValueError):
                get_webhook_repository()
        finally:
            os.unlink(db_path)
