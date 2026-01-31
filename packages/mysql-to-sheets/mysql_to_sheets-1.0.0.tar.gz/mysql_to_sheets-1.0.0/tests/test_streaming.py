"""Tests for core/streaming.py — chunked processing utilities."""

from unittest.mock import MagicMock, patch

from mysql_to_sheets.core.streaming import (
    ChunkResult,
    RowBuffer,
    StreamingConfig,
    StreamingResult,
    chunk_iterator,
    run_streaming_sync,
)


class TestStreamingConfig:
    def test_defaults(self):
        sc = StreamingConfig()
        assert sc.chunk_size == 1000
        assert sc.show_progress is True
        assert sc.progress_interval == 10

    def test_custom(self):
        sc = StreamingConfig(chunk_size=500, show_progress=False)
        assert sc.chunk_size == 500
        assert sc.show_progress is False

    def test_chunk_size_clamped_low(self):
        sc = StreamingConfig(chunk_size=10)
        assert sc.chunk_size == 100  # Clamped to minimum

    def test_chunk_size_clamped_high(self):
        sc = StreamingConfig(chunk_size=1_000_000)
        assert sc.chunk_size == 10000  # Clamped to maximum

    def test_chunk_delay_default(self):
        sc = StreamingConfig()
        assert sc.chunk_delay == 1.0

    def test_chunk_delay_custom(self):
        sc = StreamingConfig(chunk_delay=0.5)
        assert sc.chunk_delay == 0.5

    def test_chunk_delay_clamped_negative(self):
        sc = StreamingConfig(chunk_delay=-1)
        assert sc.chunk_delay == 0


class TestChunkResult:
    def test_success_default(self):
        cr = ChunkResult(chunk_number=0, rows_processed=100)
        assert cr.success is True
        assert cr.error is None

    def test_failure(self):
        cr = ChunkResult(chunk_number=1, rows_processed=0, success=False, error="boom")
        assert cr.success is False
        assert cr.error == "boom"


class TestStreamingResult:
    def test_success_property(self):
        sr = StreamingResult(total_rows=100, total_chunks=2, successful_chunks=2)
        assert sr.success is True

    def test_failure_property(self):
        sr = StreamingResult(total_rows=50, total_chunks=2, successful_chunks=1, failed_chunks=1)
        assert sr.success is False

    def test_to_dict(self):
        sr = StreamingResult(total_rows=10, total_chunks=1, successful_chunks=1)
        d = sr.to_dict()
        assert d["total_rows"] == 10
        assert d["success"] is True
        assert "chunk_results" not in d


class TestChunkIterator:
    def test_exact_division(self):
        rows = [[i] for i in range(6)]
        chunks = list(chunk_iterator(rows, 3))
        assert len(chunks) == 2
        assert len(chunks[0]) == 3
        assert len(chunks[1]) == 3

    def test_remainder(self):
        rows = [[i] for i in range(7)]
        chunks = list(chunk_iterator(rows, 3))
        assert len(chunks) == 3
        assert len(chunks[2]) == 1

    def test_empty(self):
        assert list(chunk_iterator([], 10)) == []

    def test_single_chunk(self):
        rows = [[1], [2]]
        chunks = list(chunk_iterator(rows, 100))
        assert len(chunks) == 1


class TestRowBuffer:
    def test_add_returns_false_until_full(self):
        buf = RowBuffer(max_size=3)
        assert buf.add([1]) is False
        assert buf.add([2]) is False
        assert buf.add([3]) is True

    def test_flush(self):
        buf = RowBuffer(max_size=10)
        buf.add([1])
        buf.add([2])
        rows = buf.flush()
        assert len(rows) == 2
        assert buf.is_empty

    def test_add_many(self):
        buf = RowBuffer(max_size=3)
        assert buf.add_many([[1], [2], [3]]) is True
        assert buf.size == 3

    def test_size_and_is_empty(self):
        buf = RowBuffer()
        assert buf.is_empty
        assert buf.size == 0
        buf.add([1])
        assert not buf.is_empty
        assert buf.size == 1


class TestRunStreamingSync:
    @patch("mysql_to_sheets.core.streaming.push_chunk_to_sheets")
    @patch("mysql_to_sheets.core.streaming.fetch_data_streaming")
    def test_dry_run(self, mock_fetch, mock_push):
        mock_fetch.return_value = iter(
            [
                (["id", "name"], [[1, "Alice"], [2, "Bob"]]),
            ]
        )
        config = MagicMock()
        result = run_streaming_sync(config, dry_run=True)

        assert result.success
        assert result.total_rows == 2
        assert result.total_chunks == 1
        assert result.successful_chunks == 1
        mock_push.assert_not_called()

    @patch("mysql_to_sheets.core.streaming.push_chunk_to_sheets")
    @patch("mysql_to_sheets.core.streaming.fetch_data_streaming")
    def test_push_failure_tracked(self, mock_fetch, mock_push):
        """Test that push failures are tracked in non-atomic mode."""
        mock_fetch.return_value = iter(
            [
                (["id"], [[1]]),
            ]
        )
        mock_push.side_effect = RuntimeError("Sheets error")
        config = MagicMock()
        # Use atomic=False to test the original streaming behavior
        result = run_streaming_sync(config, atomic=False)

        assert result.failed_chunks == 1
        assert not result.success
