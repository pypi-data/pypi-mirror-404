"""
Tests for JSONL Sink with Log Rotation.

Phase 4.3.2: JSONL Sink Testing

Tests:
- Basic write operations
- Log rotation by size
- Log cleanup (max files)
- Compression
- Statistics tracking
- Concurrent writes (thread safety)
- Recovery after errors
"""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from orchestrator.observability_jsonl_sink import JSONLSinkWithRotation


@pytest.fixture
def temp_dir() -> Any:
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestJSONLSinkBasic:
    """Test basic JSONL sink operations."""

    def test_write_single_event(self, temp_dir: Any) -> None:
        """Test writing single event."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl")

        event = {"timestamp": "2026-01-21T00:00:00Z", "user_id": "user123", "status": "completed"}
        sink.write(event)

        # Verify file exists and contains event
        assert (temp_dir / "test.jsonl").exists()
        with open(temp_dir / "test.jsonl", encoding="utf-8") as f:
            line = f.readline().strip()
            assert json.loads(line) == event

    def test_write_multiple_events(self, temp_dir: Any) -> None:
        """Test writing multiple events."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl")

        events = [
            {"id": 1, "status": "completed"},
            {"id": 2, "status": "failed"},
            {"id": 3, "status": "completed"},
        ]

        for event in events:
            sink.write(event)

        # Verify all events written
        with open(temp_dir / "test.jsonl", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 3
            for i, line in enumerate(lines):
                assert json.loads(line.strip()) == events[i]

    def test_write_count_tracking(self, temp_dir: Any) -> None:
        """Test write count statistics."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl")

        for i in range(5):
            sink.write({"id": i})

        stats = sink.get_stats()
        assert stats["write_count"] == 5

    def test_file_size_tracking(self, temp_dir: Any) -> None:
        """Test file size in statistics."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl")

        event = {"data": "x" * 100}
        sink.write(event)

        stats = sink.get_stats()
        assert stats["current_file_size_bytes"] > 0


class TestJSONLSinkRotation:
    """Test log rotation functionality."""

    def test_rotate_on_size_exceeded(self, temp_dir: Any) -> None:
        """Test rotation when max size is exceeded."""
        # Create sink with very small max size (1KB)
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl", max_size_mb=1)  # 1MB minimum

        # Write events until rotation occurs
        for i in range(100):
            sink.write({"id": i, "data": "x" * 100})

        # Verify rotation happened (check for compressed gz files)
        rotated_files = list(temp_dir.glob("test.*.jsonl.gz"))
        assert len(rotated_files) > 0, "No rotated compressed files found"

    def test_max_files_cleanup(self, temp_dir: Any) -> None:
        """Test cleanup of old files exceeding max_files."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl", max_size_mb=1, max_files=2)

        # Write enough data to trigger multiple rotations
        for i in range(200):
            sink.write({"id": i, "data": "x" * 100})

        # Verify max_files limit is respected
        rotated_files = list(temp_dir.glob("test.*.jsonl"))
        # Should keep current + up to max_files rotated
        assert len(rotated_files) <= 2 + 1  # +1 for current file

    def test_compression_on_rotation(self, temp_dir: Any) -> None:
        """Test that rotated files are compressed."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl", max_size_mb=1, compress=True)

        # Write enough data to trigger rotation
        for i in range(100):
            sink.write({"id": i, "data": "x" * 100})

        # Check that .gz files exist
        gz_files = list(temp_dir.glob("test.*.jsonl.gz"))
        assert len(gz_files) > 0, "No compressed files found"

    def test_no_compression_option(self, temp_dir: Any) -> None:
        """Test uncompressed rotation."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl", max_size_mb=1, compress=False)

        # Write enough data to trigger rotation
        for i in range(100):
            sink.write({"id": i, "data": "x" * 100})

        # Check that uncompressed .jsonl files exist
        uncompressed_files = list(temp_dir.glob("test.*.jsonl"))
        uncompressed_files = [f for f in uncompressed_files if not str(f).endswith(".gz")]
        assert len(uncompressed_files) > 0, "No uncompressed rotated files found"


class TestJSONLSinkStatistics:
    """Test statistics and monitoring."""

    def test_get_stats(self, temp_dir: Any) -> None:
        """Test statistics retrieval."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl")

        for i in range(10):
            sink.write({"id": i})

        stats = sink.get_stats()

        assert "current_file" in stats
        assert "write_count" in stats
        assert "current_file_size_bytes" in stats
        assert "rotated_files_count" in stats
        assert "total_size_bytes" in stats
        assert stats["write_count"] == 10

    def test_stats_with_rotated_files(self, temp_dir: Any) -> None:
        """Test statistics with rotated files."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl", max_size_mb=1, max_files=5)

        # Write data to trigger rotations
        for i in range(150):
            sink.write({"id": i, "data": "x" * 100})

        stats = sink.get_stats()

        assert stats["rotated_files_count"] > 0
        assert stats["total_size_bytes"] > 0
        assert stats["compress_enabled"] is True


class TestJSONLSinkReadRecent:
    """Test reading recent events."""

    def test_read_recent_events(self, temp_dir: Any) -> None:
        """Test reading recent events from file."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl")

        events = [{"id": i, "status": "ok"} for i in range(10)]
        for event in events:
            sink.write(event)

        # Read last 5 events
        recent = sink.read_recent_events(count=5)

        assert len(recent) == 5
        # Verify we got the last 5 events (ids 5-9)
        event_ids = [e["id"] for e in recent]
        assert 5 in event_ids and 9 in event_ids

    def test_read_recent_more_than_available(self, temp_dir: Any) -> None:
        """Test reading more events than exist."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl")

        events = [{"id": i} for i in range(3)]
        for event in events:
            sink.write(event)

        # Request 100 but only 3 exist
        recent = sink.read_recent_events(count=100)

        assert len(recent) == 3

    def test_read_recent_empty_file(self, temp_dir: Any) -> None:
        """Test reading from empty file."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl")

        recent = sink.read_recent_events(count=10)

        assert len(recent) == 0


class TestJSONLSinkThreadSafety:
    """Test thread safety."""

    def test_concurrent_writes(self, temp_dir: Any) -> None:
        """Test concurrent writes don't corrupt file."""
        from threading import Thread

        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl")

        def writer_thread(thread_id: int) -> None:
            for i in range(10):
                sink.write({"thread_id": thread_id, "iteration": i})

        # Create multiple writer threads
        threads = [Thread(target=writer_thread, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify all events written (50 total)
        # May have rotated, but total writes should be 50
        assert sink.get_stats()["write_count"] == 50


class TestJSONLSinkErrorHandling:
    """Test error handling and recovery."""

    def test_write_to_nonexistent_parent_creates_directory(self, temp_dir: Any) -> None:
        """Test automatic parent directory creation."""
        nested_path = temp_dir / "subdir" / "nested" / "test.jsonl"
        sink = JSONLSinkWithRotation(nested_path)

        sink.write({"test": "data"})

        assert nested_path.exists()
        assert sink.get_stats()["write_count"] == 1

    def test_write_invalid_json_handled(self, temp_dir: Any) -> None:
        """Test handling of non-JSON-serializable data."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl")

        class NonSerializable:
            pass

        # Should use default=str for serialization
        event = {"value": NonSerializable(), "id": 1}
        sink.write(event)

        # Verify event was written despite type
        with open(temp_dir / "test.jsonl", encoding="utf-8") as f:
            line = f.readline()
            assert "id" in line

    def test_read_malformed_lines_skipped(self, temp_dir: Any) -> None:
        """Test that malformed JSON lines are skipped."""
        filepath = temp_dir / "test.jsonl"

        # Write some valid and invalid JSON
        with open(filepath, "w", encoding="utf-8") as f:
            f.write('{"valid": true}\n')
            f.write("this is not json\n")
            f.write('{"also_valid": 123}\n')

        sink = JSONLSinkWithRotation(filepath)
        recent = sink.read_recent_events(count=10)

        # Should skip the invalid line
        assert len(recent) == 2


class TestJSONLSinkConfiguration:
    """Test configuration options."""

    def test_custom_max_files(self, temp_dir: Any) -> None:
        """Test custom max_files configuration."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl", max_size_mb=1, max_files=3)

        stats_init = sink.get_stats()
        assert stats_init["max_files"] == 3

    def test_custom_encoding(self, temp_dir: Any) -> None:
        """Test custom encoding configuration."""
        sink = JSONLSinkWithRotation(temp_dir / "test.jsonl", encoding="utf-8")

        event = {"text": "Unicode test: 你好世界"}
        sink.write(event)

        # Verify unicode handled correctly
        recent = sink.read_recent_events(count=1)
        assert recent[0]["text"] == "Unicode test: 你好世界"
