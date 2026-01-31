"""Tests for cache.py thread safety and data handling"""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from ..cache import (
    AtomicViewId,
    CacheReady,
    CacheReadyState,
    DataCacheContext,
    ViewParams,
)


class TestAtomicViewId:
    """Tests for the AtomicViewId class thread safety"""

    def test_initial_value_is_zero(self):
        """AtomicViewId should initialize to 0"""
        view_id = AtomicViewId()
        assert view_id.get() == 0

    def test_increment_returns_old_value(self):
        """increment() should return the old value before incrementing"""
        view_id = AtomicViewId()
        assert view_id.increment() == 0
        assert view_id.get() == 1
        assert view_id.increment() == 1
        assert view_id.get() == 2

    def test_sequential_increments(self):
        """Multiple increments should produce sequential values"""
        view_id = AtomicViewId()
        for i in range(100):
            old_val = view_id.increment()
            assert old_val == i
        assert view_id.get() == 100

    def test_thread_safety_concurrent_increments(self):
        """Concurrent increments from multiple threads should not lose updates"""
        view_id = AtomicViewId()
        num_threads = 10
        increments_per_thread = 100
        expected_final = num_threads * increments_per_thread

        def worker():
            for _ in range(increments_per_thread):
                view_id.increment()

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert view_id.get() == expected_final

    def test_thread_safety_concurrent_get_and_increment(self):
        """Concurrent get() and increment() operations should be safe"""
        view_id = AtomicViewId()
        results = []
        errors = []

        def incrementer():
            for _ in range(50):
                try:
                    view_id.increment()
                except Exception as e:
                    errors.append(e)

        def reader():
            for _ in range(50):
                try:
                    val = view_id.get()
                    results.append(val)
                except Exception as e:
                    errors.append(e)

        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=incrementer))
            threads.append(threading.Thread(target=reader))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"
        # All read values should be valid (non-negative integers)
        assert all(isinstance(v, int) and v >= 0 for v in results)


class TestCacheReadyState:
    """Tests for CacheReadyState enum"""

    def test_state_values(self):
        """CacheReadyState should have the expected values"""
        assert CacheReadyState.Unprimed.value == 0
        assert CacheReadyState.Wait.value == 3
        assert CacheReadyState.Primed.value == 4


class TestCacheReady:
    """Tests for the CacheReady state machine"""

    @pytest.fixture
    def mock_cache(self):
        """Create a mock DataCache for testing"""
        cache = MagicMock()
        cache.signal_data = MagicMock()
        cache.signal_data.emit = MagicMock()
        return cache

    def test_initial_state_is_primed(self, mock_cache):
        """CacheReady should start in Primed state"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)
        assert ready.state == CacheReadyState.Primed

    def test_request_fire_from_primed_fires_immediately(self, mock_cache):
        """request_fire() from Primed state should emit signal and transition to Unprimed"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)

        ready.request_fire("test_command")

        mock_cache.signal_data.emit.assert_called_once_with("test_command")
        assert ready.state == CacheReadyState.Unprimed

    def test_request_fire_from_unprimed_does_not_fire(self, mock_cache):
        """request_fire() from Unprimed state should not emit signal"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)
        ready.state = CacheReadyState.Unprimed

        ready.request_fire("test_command")

        mock_cache.signal_data.emit.assert_not_called()
        assert ready.state == CacheReadyState.Unprimed

    def test_request_fire_from_wait_does_not_fire(self, mock_cache):
        """request_fire() from Wait state should not emit signal"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)
        ready.state = CacheReadyState.Wait

        ready.request_fire("test_command")

        mock_cache.signal_data.emit.assert_not_called()
        assert ready.state == CacheReadyState.Wait

    def test_prime_from_unprimed_transitions_to_wait(self, mock_cache):
        """prime() from Unprimed state should transition to Wait"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)
        ready.state = CacheReadyState.Unprimed

        # Mock the timer to avoid actual delays
        with patch.object(ready, "_start_delay"):
            ready.prime()

        assert ready.state == CacheReadyState.Wait

    def test_prime_from_wait_stays_in_wait(self, mock_cache):
        """prime() from Wait state should stay in Wait"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)
        ready.state = CacheReadyState.Wait

        ready.prime()

        assert ready.state == CacheReadyState.Wait

    def test_prime_from_primed_stays_primed(self, mock_cache):
        """prime() from Primed state should stay in Primed"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)

        ready.prime()

        assert ready.state == CacheReadyState.Primed

    def test_delay_done_with_commands_fires(self, mock_cache):
        """_delay_done() in Wait state with commands should fire and transition to Unprimed"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)
        ready.state = CacheReadyState.Wait
        ready.commands = ["cmd1"]

        ready._delay_done()

        mock_cache.signal_data.emit.assert_called_once_with("cmd1")
        assert ready.state == CacheReadyState.Unprimed

    def test_delay_done_without_commands_transitions_to_primed(self, mock_cache):
        """_delay_done() in Wait state without commands should transition to Primed"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)
        ready.state = CacheReadyState.Wait
        ready.commands = []

        ready._delay_done()

        mock_cache.signal_data.emit.assert_not_called()
        assert ready.state == CacheReadyState.Primed

    def test_command_queue_maintains_order(self, mock_cache):
        """Commands should be processed in LIFO order (most recent first)"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)
        ready.commands = ["cmd1", "cmd2", "cmd3"]

        # _fire pops from the end
        ready._fire()
        mock_cache.signal_data.emit.assert_called_with("cmd3")
        assert ready.commands == ["cmd1", "cmd2"]

    def test_add_command_deduplicates_first_position(self, mock_cache):
        """_add_command should deduplicate when same command is at front"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)
        ready.commands = ["cmd1"]

        ready._add_command("cmd1")

        assert ready.commands == ["cmd1"]

    def test_add_command_prepends_different_command(self, mock_cache):
        """_add_command should prepend when different command"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)
        ready.commands = ["cmd1"]

        ready._add_command("cmd2")

        assert ready.commands == ["cmd2", "cmd1"]

    def test_thread_safety_request_fire_concurrent(self, mock_cache):
        """Concurrent request_fire calls should not cause race conditions"""
        ready = CacheReady(delay_ms=1, cache=mock_cache)
        errors = []

        def worker(cmd):
            try:
                for _ in range(10):
                    ready.request_fire(cmd)
                    ready.prime()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(f"cmd{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"

    def test_invalid_state_raises_error(self, mock_cache):
        """Invalid state should raise ValueError"""
        ready = CacheReady(delay_ms=10, cache=mock_cache)
        ready.state = MagicMock()  # Invalid state

        with pytest.raises(ValueError, match="unrecognized CacheReadyState"):
            ready.request_fire("cmd")


class TestDataCacheContext:
    """Tests for the DataCacheContext context manager"""

    @pytest.fixture
    def mock_cache(self):
        """Create a mock DataCache for testing"""
        cache = MagicMock()
        cache._new_scope_view = MagicMock()
        cache.signal_channel_change = MagicMock()
        cache.signal_channel_change.emit = MagicMock()
        cache.context_nest_level = 0
        cache.next_view_params = ViewParams(False, False, 0, False, False, set(), 0, 0)
        cache.prev_view_params = ViewParams(False, False, 0, False, False, set(), 0, 0)
        return cache

    def test_context_manager_no_change(self, mock_cache):
        """Context manager should not trigger update if channels unchanged"""
        context = DataCacheContext(mock_cache)

        with context:
            mock_cache.next_view_params.channels = set()

        mock_cache._new_scope_view.assert_not_called()

    def test_context_manager_with_change(self, mock_cache):
        """Context manager should trigger update if channels changed"""
        mock_cache.get_channels = MagicMock(return_value={"chan1"})
        context = DataCacheContext(mock_cache)

        with context:
            mock_cache.next_view_params.channels = {"chan1"}

        mock_cache._new_scope_view.assert_called_once()
        mock_cache.signal_channel_change.emit.assert_called_once_with(None)

    def test_context_manager_with_force(self, mock_cache):
        """Context manager with force=True should always trigger update"""
        context = DataCacheContext(mock_cache, force=True)

        with context:
            pass

        mock_cache._new_scope_view.assert_called_once()

    def test_force_method(self, mock_cache):
        """force() method should set the force flag"""
        context = DataCacheContext(mock_cache)
        assert context._force is False

        context.force(True)
        assert context._force is True

        context.force(False)
        assert context._force is False

    def test_getattr_delegation(self, mock_cache):
        """__getattr__ should delegate to cache"""
        mock_cache.some_attribute = "test_value"
        context = DataCacheContext(mock_cache)

        assert context.some_attribute == "test_value"
