"""Tests for the SerialDispatcher class.

These tests run without hardware by using mock serial ports.
"""

import threading
import time
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from sphero_rvr_mcp.protocol.dispatcher import SerialDispatcher, PendingRequest
from sphero_rvr_mcp.protocol.packet import (
    build_packet, parse_response, get_packet_header,
    SOP, EOP, DID_POWER, TARGET_BT
)


class MockSerial:
    """Mock serial port for testing."""

    def __init__(self):
        self._is_open = True
        self._input_buffer = BytesIO()
        self._output_buffer = BytesIO()
        self._lock = threading.Lock()

    @property
    def is_open(self):
        return self._is_open

    def close(self):
        self._is_open = False

    @property
    def in_waiting(self):
        with self._lock:
            current = self._input_buffer.tell()
            self._input_buffer.seek(0, 2)  # End
            end = self._input_buffer.tell()
            self._input_buffer.seek(current)
            return end - current

    def read(self, size=1):
        with self._lock:
            return self._input_buffer.read(size)

    def write(self, data):
        with self._lock:
            return self._output_buffer.write(data)

    def flush(self):
        pass

    def inject_response(self, data: bytes):
        """Inject data into the input buffer (simulates RVR response)."""
        with self._lock:
            current = self._input_buffer.tell()
            self._input_buffer.seek(0, 2)  # End
            self._input_buffer.write(data)
            self._input_buffer.seek(current)


class TestPendingRequest:
    """Tests for PendingRequest dataclass."""

    def test_is_expired_false(self):
        """Test that new request is not expired."""
        from concurrent.futures import Future
        req = PendingRequest(
            future=Future(),
            did=0x13,
            cid=0x10,
            seq=1,
            timeout=5.0
        )
        assert not req.is_expired()

    def test_is_expired_true(self):
        """Test that old request is expired."""
        from concurrent.futures import Future
        req = PendingRequest(
            future=Future(),
            did=0x13,
            cid=0x10,
            seq=1,
            timeout=0.01,
            created_at=time.time() - 1.0
        )
        assert req.is_expired()


class TestSerialDispatcher:
    """Tests for SerialDispatcher class."""

    def test_start_stop(self):
        """Test starting and stopping the dispatcher."""
        mock_serial = MockSerial()
        dispatcher = SerialDispatcher(mock_serial)

        assert dispatcher.start()
        assert dispatcher._running
        assert dispatcher._reader_thread.is_alive()

        # Starting again should return False
        assert not dispatcher.start()

        assert dispatcher.stop()
        assert not dispatcher._running

    def test_register_notification_handler(self):
        """Test registering and unregistering notification handlers."""
        mock_serial = MockSerial()
        dispatcher = SerialDispatcher(mock_serial)

        handler_called = []

        def handler(response):
            handler_called.append(response)

        dispatcher.register_notification_handler(0x13, 0x10, handler)
        assert (0x13, 0x10) in dispatcher._notification_handlers

        assert dispatcher.unregister_notification_handler(0x13, 0x10)
        assert (0x13, 0x10) not in dispatcher._notification_handlers

        # Unregistering non-existent handler returns False
        assert not dispatcher.unregister_notification_handler(0x99, 0x99)

    def test_get_stats(self):
        """Test getting dispatcher statistics."""
        mock_serial = MockSerial()
        dispatcher = SerialDispatcher(mock_serial)

        stats = dispatcher.get_stats()
        assert 'packets_received' in stats
        assert 'packets_dispatched' in stats
        assert 'packets_dropped' in stats
        assert 'timeouts' in stats
        assert 'notifications' in stats


class TestGetPacketHeader:
    """Tests for get_packet_header function."""

    def test_extract_header_from_standard_packet(self):
        """Test extracting header from a standard packet."""
        # Build a packet with known values
        packet = build_packet(0x13, 0x10, 0x01, b'', request_response=True)
        did, cid, seq = get_packet_header(packet)

        assert did == 0x13  # DID_POWER
        assert cid == 0x10  # CID_GET_BATTERY_PERCENTAGE

    def test_extract_header_short_packet(self):
        """Test error on too-short packet."""
        with pytest.raises(ValueError, match="too short"):
            get_packet_header(b'\x8d')

    def test_extract_header_no_sop(self):
        """Test error when no SOP found."""
        with pytest.raises(ValueError, match="Invalid SOP"):
            get_packet_header(b'\x00\x01\x02\x03\xd8')

    def test_extract_header_no_eop(self):
        """Test error when no EOP found."""
        with pytest.raises(ValueError, match="No EOP"):
            get_packet_header(b'\x8d\x01\x02\x03\x04')


class TestDispatcherIntegration:
    """Integration tests for dispatcher with mock serial."""

    def test_send_and_wait_no_dispatcher(self):
        """Test that send_and_wait returns None when dispatcher not running."""
        mock_serial = MockSerial()
        dispatcher = SerialDispatcher(mock_serial)
        # Don't start the dispatcher

        packet = build_packet(0x13, 0x10, 0x01, b'', request_response=True)
        did, cid, seq = get_packet_header(packet)

        result = dispatcher.send_and_wait(packet, did, cid, seq, timeout=0.1)
        assert result is None

    def test_cleanup_expired_requests(self):
        """Test that expired requests are cleaned up."""
        mock_serial = MockSerial()
        dispatcher = SerialDispatcher(mock_serial)

        # Manually add an expired request
        from concurrent.futures import Future
        expired_req = PendingRequest(
            future=Future(),
            did=0x13,
            cid=0x10,
            seq=99,
            timeout=0.001,
            created_at=time.time() - 1.0
        )
        dispatcher._pending[99] = expired_req

        # Cleanup should remove it
        dispatcher._cleanup_expired()
        assert 99 not in dispatcher._pending


class TestPacketProcessing:
    """Tests for packet processing logic."""

    def test_process_complete_packet(self):
        """Test processing a complete packet."""
        mock_serial = MockSerial()
        dispatcher = SerialDispatcher(mock_serial)

        # Create a mock response packet
        # Response packet format: SOP + escaped content + EOP
        # Content: flags, target, source, did, cid, seq, data, checksum
        # For simplicity, we'll use parse_response to verify our test packet

        # Build a simple response packet (as if from RVR)
        # Response flag = 0x01
        flags = 0x31  # IS_RESPONSE | HAS_TARGET | HAS_SOURCE
        target = 0x00  # Host
        source = 0x01  # BT
        did = 0x13
        cid = 0x10
        seq = 5
        data = b'\x64'  # Battery percentage 100

        content = bytes([flags, target, source, did, cid, seq]) + data
        chk = (~(sum(content) % 256)) & 0xFF
        response_packet = bytes([SOP]) + content + bytes([chk, EOP])

        # Process the data
        dispatcher._process_data(response_packet)

        # Verify stats
        assert dispatcher._stats['packets_received'] == 1
