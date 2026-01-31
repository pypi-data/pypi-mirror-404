"""Tests for the MovementTracker class.

These tests run without hardware.
"""

import threading
import time
from concurrent.futures import Future
from unittest.mock import MagicMock

import pytest

from sphero_rvr_mcp.protocol.movement import MovementTracker, CID_XY_POSITION_DRIVE_RESULT_NOTIFY
from sphero_rvr_mcp.protocol.packet import ParsedResponse, DID_DRIVE


class MockDispatcher:
    """Mock dispatcher for testing."""

    def __init__(self):
        self.handlers = {}

    def register_notification_handler(self, did, cid, handler):
        self.handlers[(did, cid)] = handler

    def unregister_notification_handler(self, did, cid):
        if (did, cid) in self.handlers:
            del self.handlers[(did, cid)]
            return True
        return False

    def trigger_notification(self, did, cid, response):
        """Simulate receiving a notification."""
        handler = self.handlers.get((did, cid))
        if handler:
            handler(response)


class TestMovementTracker:
    """Tests for MovementTracker class."""

    def test_register_with_dispatcher(self):
        """Test registering with dispatcher."""
        dispatcher = MockDispatcher()
        tracker = MovementTracker()

        tracker.register_with_dispatcher(dispatcher)

        assert (DID_DRIVE, CID_XY_POSITION_DRIVE_RESULT_NOTIFY) in dispatcher.handlers

    def test_unregister_from_dispatcher(self):
        """Test unregistering from dispatcher."""
        dispatcher = MockDispatcher()
        tracker = MovementTracker()

        tracker.register_with_dispatcher(dispatcher)
        tracker.unregister_from_dispatcher(dispatcher)

        assert (DID_DRIVE, CID_XY_POSITION_DRIVE_RESULT_NOTIFY) not in dispatcher.handlers

    def test_start_movement_returns_future(self):
        """Test that start_movement returns a Future."""
        tracker = MovementTracker()
        future = tracker.start_movement(timeout=5.0)

        assert isinstance(future, Future)
        assert tracker._stats['movements_started'] == 1

    def test_start_movement_cancels_previous(self):
        """Test that starting a new movement cancels the previous one."""
        tracker = MovementTracker()

        future1 = tracker.start_movement(timeout=5.0)
        future2 = tracker.start_movement(timeout=5.0)

        # First future should be cancelled with exception
        with pytest.raises(RuntimeError, match="cancelled"):
            future1.result(timeout=0.1)

        assert not future2.done()

    def test_wait_for_completion_success(self):
        """Test waiting for successful completion."""
        dispatcher = MockDispatcher()
        tracker = MovementTracker()
        tracker.register_with_dispatcher(dispatcher)

        # Start movement
        tracker.start_movement(timeout=5.0)

        # Simulate completion notification in another thread
        def send_notification():
            time.sleep(0.1)
            response = ParsedResponse(
                flags=0x01,
                did=DID_DRIVE,
                cid=CID_XY_POSITION_DRIVE_RESULT_NOTIFY,
                seq=1,
                data=b'\x00'  # Success
            )
            dispatcher.trigger_notification(DID_DRIVE, CID_XY_POSITION_DRIVE_RESULT_NOTIFY, response)

        thread = threading.Thread(target=send_notification)
        thread.start()

        # Wait for completion
        result = tracker.wait_for_completion(timeout=2.0)

        thread.join()
        assert result is True
        assert tracker._stats['movements_completed'] == 1

    def test_wait_for_completion_timeout_with_fallback(self):
        """Test timeout with fallback time."""
        tracker = MovementTracker()

        # Start movement
        tracker.start_movement(timeout=5.0)

        # Wait should use fallback time
        start = time.time()
        result = tracker.wait_for_completion(timeout=0.1, fallback_time=0.2)
        elapsed = time.time() - start

        # Should have waited roughly fallback_time
        assert result is True  # With fallback, returns True
        assert elapsed >= 0.15  # Accounts for initial timeout wait
        assert tracker._stats['movements_timed_out'] == 1

    def test_wait_for_completion_timeout_no_fallback(self):
        """Test timeout without fallback."""
        tracker = MovementTracker()

        tracker.start_movement(timeout=0.1)

        result = tracker.wait_for_completion(timeout=0.1, fallback_time=None)

        assert result is False
        assert tracker._stats['movements_timed_out'] == 1

    def test_wait_for_completion_no_movement(self):
        """Test waiting when no movement in progress."""
        tracker = MovementTracker()

        result = tracker.wait_for_completion(timeout=0.1)

        assert result is False

    def test_cancel_movement(self):
        """Test cancelling a movement."""
        tracker = MovementTracker()

        future = tracker.start_movement(timeout=5.0)
        tracker.cancel_movement()

        with pytest.raises(RuntimeError, match="cancelled"):
            future.result(timeout=0.1)

    def test_get_last_result(self):
        """Test getting the last movement result."""
        dispatcher = MockDispatcher()
        tracker = MovementTracker()
        tracker.register_with_dispatcher(dispatcher)

        # Initially None
        assert tracker.get_last_result() is None

        # Start and complete a movement
        tracker.start_movement(timeout=5.0)
        response = ParsedResponse(
            flags=0x01,
            did=DID_DRIVE,
            cid=CID_XY_POSITION_DRIVE_RESULT_NOTIFY,
            seq=1,
            data=b'\x00'
        )
        dispatcher.trigger_notification(DID_DRIVE, CID_XY_POSITION_DRIVE_RESULT_NOTIFY, response)

        result = tracker.get_last_result()
        assert result is not None
        assert result['completed'] is True
        assert 'duration' in result

    def test_get_stats(self):
        """Test getting statistics."""
        tracker = MovementTracker()

        stats = tracker.get_stats()

        assert 'movements_started' in stats
        assert 'movements_completed' in stats
        assert 'movements_timed_out' in stats
