"""Tests for SyncContext component dataclasses.

This module tests the new SyncContext refactoring that splits the
god object into focused components:
- SyncOptions (frozen) - Immutable execution options
- SyncMetadata (frozen) - Immutable tracking info
- SyncFeatureConfigs - Optional feature configurations
- SyncState - Mutable pipeline state
"""

import logging
import time
from unittest.mock import MagicMock

import pytest

from mysql_to_sheets.core.sync.protocols import (
    SyncContext,
    SyncFeatureConfigs,
    SyncMetadata,
    SyncOptions,
    SyncState,
)


class TestSyncOptions:
    """Tests for SyncOptions frozen dataclass."""

    def test_default_values(self):
        """Verify SyncOptions has correct defaults."""
        options = SyncOptions()

        assert options.mode == "replace"
        assert options.chunk_size == 1000
        assert options.dry_run is False
        assert options.preview is False
        assert options.atomic is True
        assert options.preserve_gid is False
        assert options.resumable is False
        assert options.job_id is None
        assert options.notify is None
        assert options.schema_policy is None
        assert options.expected_headers is None
        assert options.detect_pii is None
        assert options.pii_acknowledged is False
        assert options.create_worksheet is None
        assert options.skip_snapshot is False

    def test_custom_values(self):
        """Verify SyncOptions accepts custom values."""
        options = SyncOptions(
            mode="streaming",
            chunk_size=500,
            dry_run=True,
            preview=True,
            atomic=False,
            preserve_gid=True,
            resumable=True,
            job_id=42,
            notify=True,
            schema_policy="additive",
            expected_headers=("id", "name", "email"),
            detect_pii=True,
            pii_acknowledged=True,
            create_worksheet=True,
            skip_snapshot=True,
        )

        assert options.mode == "streaming"
        assert options.chunk_size == 500
        assert options.dry_run is True
        assert options.job_id == 42
        assert options.expected_headers == ("id", "name", "email")

    def test_is_frozen(self):
        """Verify SyncOptions cannot be modified after creation."""
        options = SyncOptions()

        with pytest.raises(AttributeError):
            options.mode = "streaming"

        with pytest.raises(AttributeError):
            options.dry_run = True

    def test_is_hashable(self):
        """Verify SyncOptions can be used as dict key (frozen = hashable)."""
        options1 = SyncOptions(mode="replace")
        options2 = SyncOptions(mode="streaming")

        # Should be usable as dict keys
        cache = {options1: "cached_result_1", options2: "cached_result_2"}

        assert cache[options1] == "cached_result_1"
        assert cache[options2] == "cached_result_2"

    def test_expected_headers_is_tuple(self):
        """Verify expected_headers uses tuple for hashability."""
        options = SyncOptions(expected_headers=("id", "name"))

        assert isinstance(options.expected_headers, tuple)
        # Tuple is hashable, list would not be
        hash(options)


class TestSyncMetadata:
    """Tests for SyncMetadata frozen dataclass."""

    def test_default_values(self):
        """Verify SyncMetadata has correct defaults."""
        metadata = SyncMetadata()

        assert metadata.sync_id == ""
        assert metadata.organization_id is None
        assert metadata.config_name is None
        assert metadata.config_id is None
        assert metadata.source == "sync"
        assert metadata.start_time == 0.0

    def test_custom_values(self):
        """Verify SyncMetadata accepts custom values."""
        metadata = SyncMetadata(
            sync_id="abc-123",
            organization_id=1,
            config_name="daily-sales",
            config_id=42,
            source="api",
            start_time=1700000000.0,
        )

        assert metadata.sync_id == "abc-123"
        assert metadata.organization_id == 1
        assert metadata.config_name == "daily-sales"
        assert metadata.config_id == 42
        assert metadata.source == "api"
        assert metadata.start_time == 1700000000.0

    def test_is_frozen(self):
        """Verify SyncMetadata cannot be modified after creation."""
        metadata = SyncMetadata()

        with pytest.raises(AttributeError):
            metadata.sync_id = "new-id"

        with pytest.raises(AttributeError):
            metadata.organization_id = 99

    def test_generate_classmethod(self):
        """Verify SyncMetadata.generate() creates valid metadata."""
        before = time.time()
        metadata = SyncMetadata.generate(
            organization_id=1,
            config_name="test-config",
            config_id=5,
            source="api",
        )
        after = time.time()

        # sync_id should be UUID format
        assert len(metadata.sync_id) == 36  # UUID format: 8-4-4-4-12
        assert "-" in metadata.sync_id

        # start_time should be current time
        assert before <= metadata.start_time <= after

        # Custom values preserved
        assert metadata.organization_id == 1
        assert metadata.config_name == "test-config"
        assert metadata.config_id == 5
        assert metadata.source == "api"

    def test_generate_with_defaults(self):
        """Verify SyncMetadata.generate() uses correct defaults."""
        metadata = SyncMetadata.generate()

        assert len(metadata.sync_id) == 36
        assert metadata.organization_id is None
        assert metadata.config_name is None
        assert metadata.config_id is None
        assert metadata.source == "sync"
        assert metadata.start_time > 0


class TestSyncFeatureConfigs:
    """Tests for SyncFeatureConfigs dataclass."""

    def test_default_values(self):
        """Verify SyncFeatureConfigs has None defaults."""
        features = SyncFeatureConfigs()

        assert features.incremental_config is None
        assert features.column_mapping_config is None
        assert features.pii_config is None

    def test_accepts_config_objects(self):
        """Verify SyncFeatureConfigs stores config objects."""
        mock_incremental = MagicMock()
        mock_column_mapping = MagicMock()
        mock_pii = MagicMock()

        features = SyncFeatureConfigs(
            incremental_config=mock_incremental,
            column_mapping_config=mock_column_mapping,
            pii_config=mock_pii,
        )

        assert features.incremental_config is mock_incremental
        assert features.column_mapping_config is mock_column_mapping
        assert features.pii_config is mock_pii

    def test_is_mutable(self):
        """Verify SyncFeatureConfigs is mutable (not frozen)."""
        features = SyncFeatureConfigs()

        mock_config = MagicMock()
        features.incremental_config = mock_config

        assert features.incremental_config is mock_config


class TestSyncState:
    """Tests for SyncState mutable dataclass."""

    def test_default_values(self):
        """Verify SyncState has empty defaults."""
        state = SyncState()

        assert state.headers == []
        assert state.rows == []
        assert state.cleaned_rows == []
        assert state.schema_changes is None
        assert state.pii_detection_result is None
        assert state.step_warnings == []

    def test_is_mutable(self):
        """Verify SyncState can be modified."""
        state = SyncState()

        state.headers = ["id", "name"]
        state.rows = [[1, "Alice"], [2, "Bob"]]
        state.cleaned_rows = [[1, "Alice"], [2, "Bob"]]
        state.schema_changes = {"has_changes": True}
        state.pii_detection_result = {"email": "detected"}

        assert state.headers == ["id", "name"]
        assert len(state.rows) == 2
        assert state.schema_changes["has_changes"] is True

    def test_add_warning(self):
        """Verify add_warning() appends to step_warnings."""
        state = SyncState()

        state.add_warning("First warning")
        state.add_warning("Second warning")

        assert len(state.step_warnings) == 2
        assert "First warning" in state.step_warnings
        assert "Second warning" in state.step_warnings

    def test_clear(self):
        """Verify clear() resets all state."""
        state = SyncState(
            headers=["id", "name"],
            rows=[[1, "Alice"]],
            cleaned_rows=[[1, "Alice"]],
            schema_changes={"has_changes": True},
            pii_detection_result={"email": "detected"},
            step_warnings=["Warning 1"],
        )

        state.clear()

        assert state.headers == []
        assert state.rows == []
        assert state.cleaned_rows == []
        assert state.schema_changes is None
        assert state.pii_detection_result is None
        assert state.step_warnings == []


class TestSyncContext:
    """Tests for SyncContext backward compatibility and new API."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock Config object."""
        return MagicMock()

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return logging.getLogger("test")

    def test_basic_creation(self, mock_config, mock_logger):
        """Verify SyncContext can be created with required args only."""
        ctx = SyncContext(config=mock_config, logger=mock_logger)

        assert ctx.config is mock_config
        assert ctx.logger is mock_logger
        # Components should have defaults
        assert isinstance(ctx.options, SyncOptions)
        assert isinstance(ctx.metadata, SyncMetadata)
        assert isinstance(ctx.features, SyncFeatureConfigs)
        assert isinstance(ctx.state, SyncState)

    def test_backward_compat_flat_attributes(self, mock_config, mock_logger):
        """Verify flat attributes still work for backward compatibility."""
        ctx = SyncContext(
            config=mock_config,
            logger=mock_logger,
            mode="streaming",
            chunk_size=500,
            dry_run=True,
            organization_id=1,
            config_name="test",
        )

        # Flat attributes accessible
        assert ctx.mode == "streaming"
        assert ctx.chunk_size == 500
        assert ctx.dry_run is True
        assert ctx.organization_id == 1
        assert ctx.config_name == "test"

        # Also synced to component objects
        assert ctx.options.mode == "streaming"
        assert ctx.options.chunk_size == 500
        assert ctx.options.dry_run is True
        assert ctx.metadata.organization_id == 1
        assert ctx.metadata.config_name == "test"

    def test_state_mutation(self, mock_config, mock_logger):
        """Verify state can be mutated via flat attributes."""
        ctx = SyncContext(config=mock_config, logger=mock_logger)

        # Mutate via flat attributes (backward compat)
        ctx.headers = ["id", "name"]
        ctx.rows = [[1, "Alice"]]

        # Changes reflected in flat attributes
        assert ctx.headers == ["id", "name"]
        assert ctx.rows == [[1, "Alice"]]

    def test_step_warnings_mutation(self, mock_config, mock_logger):
        """Verify step_warnings can be mutated."""
        ctx = SyncContext(config=mock_config, logger=mock_logger)

        ctx.step_warnings.append("Warning 1")
        ctx.step_warnings.append("Warning 2")

        assert len(ctx.step_warnings) == 2
        assert "Warning 1" in ctx.step_warnings

    def test_create_classmethod(self, mock_config, mock_logger):
        """Verify SyncContext.create() factory method."""
        options = SyncOptions(mode="streaming", chunk_size=500)
        metadata = SyncMetadata.generate(organization_id=1, source="api")

        ctx = SyncContext.create(
            config=mock_config,
            logger=mock_logger,
            options=options,
            metadata=metadata,
        )

        # Component objects have same values (may not be same reference due to sync)
        assert ctx.options.mode == options.mode
        assert ctx.options.chunk_size == options.chunk_size
        assert ctx.metadata.sync_id == metadata.sync_id
        assert ctx.metadata.organization_id == metadata.organization_id

        # Flat attributes synced from components
        assert ctx.mode == "streaming"
        assert ctx.chunk_size == 500
        assert ctx.organization_id == 1
        assert ctx.source == "api"
        assert ctx.sync_id == metadata.sync_id

    def test_create_with_defaults(self, mock_config, mock_logger):
        """Verify SyncContext.create() generates metadata if not provided."""
        ctx = SyncContext.create(config=mock_config, logger=mock_logger)

        # metadata should be auto-generated
        assert len(ctx.sync_id) == 36  # UUID
        assert ctx.metadata.start_time > 0

        # options and features have defaults
        assert ctx.options.mode == "replace"
        assert ctx.features.incremental_config is None

    def test_expected_headers_list_to_tuple(self, mock_config, mock_logger):
        """Verify expected_headers list is converted to tuple in options."""
        ctx = SyncContext(
            config=mock_config,
            logger=mock_logger,
            expected_headers=["id", "name", "email"],
        )

        # Flat attribute is list (backward compat)
        assert ctx.expected_headers == ["id", "name", "email"]

        # Component uses tuple (hashable)
        assert ctx.options.expected_headers == ("id", "name", "email")

    def test_expected_headers_tuple_in_create(self, mock_config, mock_logger):
        """Verify create() converts tuple back to list for backward compat."""
        options = SyncOptions(expected_headers=("id", "name"))

        ctx = SyncContext.create(
            config=mock_config,
            logger=mock_logger,
            options=options,
        )

        # Flat attribute should be list for backward compat
        assert ctx.expected_headers == ["id", "name"]
        assert isinstance(ctx.expected_headers, list)

        # Component keeps tuple
        assert ctx.options.expected_headers == ("id", "name")

    def test_all_options_synced(self, mock_config, mock_logger):
        """Verify all option fields are synced to components."""
        ctx = SyncContext(
            config=mock_config,
            logger=mock_logger,
            mode="append",
            chunk_size=2000,
            dry_run=True,
            preview=True,
            atomic=False,
            preserve_gid=True,
            resumable=True,
            job_id=99,
            notify=True,
            schema_policy="flexible",
            expected_headers=["a", "b"],
            detect_pii=True,
            pii_acknowledged=True,
            create_worksheet=True,
            skip_snapshot=True,
        )

        # All should be in options
        assert ctx.options.mode == "append"
        assert ctx.options.chunk_size == 2000
        assert ctx.options.dry_run is True
        assert ctx.options.preview is True
        assert ctx.options.atomic is False
        assert ctx.options.preserve_gid is True
        assert ctx.options.resumable is True
        assert ctx.options.job_id == 99
        assert ctx.options.notify is True
        assert ctx.options.schema_policy == "flexible"
        assert ctx.options.expected_headers == ("a", "b")
        assert ctx.options.detect_pii is True
        assert ctx.options.pii_acknowledged is True
        assert ctx.options.create_worksheet is True
        assert ctx.options.skip_snapshot is True

    def test_all_metadata_synced(self, mock_config, mock_logger):
        """Verify all metadata fields are synced to components."""
        ctx = SyncContext(
            config=mock_config,
            logger=mock_logger,
            sync_id="test-sync-123",
            organization_id=5,
            config_name="daily-report",
            config_id=10,
            source="scheduler",
            start_time=1700000000.0,
        )

        assert ctx.metadata.sync_id == "test-sync-123"
        assert ctx.metadata.organization_id == 5
        assert ctx.metadata.config_name == "daily-report"
        assert ctx.metadata.config_id == 10
        assert ctx.metadata.source == "scheduler"
        assert ctx.metadata.start_time == 1700000000.0

    def test_features_synced(self, mock_config, mock_logger):
        """Verify feature configs are synced to components."""
        mock_incremental = MagicMock()
        mock_column_mapping = MagicMock()
        mock_pii = MagicMock()

        ctx = SyncContext(
            config=mock_config,
            logger=mock_logger,
            incremental_config=mock_incremental,
            column_mapping_config=mock_column_mapping,
            pii_config=mock_pii,
        )

        assert ctx.features.incremental_config is mock_incremental
        assert ctx.features.column_mapping_config is mock_column_mapping
        assert ctx.features.pii_config is mock_pii


class TestSyncContextStateSharing:
    """Tests for state reference sharing between flat and component."""

    @pytest.fixture
    def ctx(self):
        """Create a SyncContext for testing."""
        return SyncContext(
            config=MagicMock(),
            logger=logging.getLogger("test"),
        )

    def test_headers_reference_shared(self, ctx):
        """Verify headers list is shared between flat and state."""
        # Modify via flat attribute
        ctx.headers.append("id")
        ctx.headers.append("name")

        # State should reflect change (same reference)
        assert ctx.state.headers == ["id", "name"]

    def test_rows_reference_shared(self, ctx):
        """Verify rows list is shared between flat and state."""
        ctx.rows.append([1, "Alice"])
        ctx.rows.append([2, "Bob"])

        assert len(ctx.state.rows) == 2
        assert ctx.state.rows[0] == [1, "Alice"]

    def test_step_warnings_reference_shared(self, ctx):
        """Verify step_warnings is shared between flat and state."""
        ctx.step_warnings.append("Warning from flat")
        ctx.state.add_warning("Warning from state")

        # Both methods add to same list
        assert len(ctx.step_warnings) == 2
        assert len(ctx.state.step_warnings) == 2
