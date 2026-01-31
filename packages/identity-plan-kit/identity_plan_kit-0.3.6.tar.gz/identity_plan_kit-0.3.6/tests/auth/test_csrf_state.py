"""Tests for CSRF state validation (P0 security fix)."""

import pytest

from identity_plan_kit.shared.state_store import InMemoryStateStore

pytestmark = pytest.mark.anyio


class TestCSRFStateValidation:
    """Test suite for OAuth CSRF state management."""

    @pytest.fixture
    async def store(self) -> InMemoryStateStore:
        """Create a fresh state store for each test."""
        store = InMemoryStateStore()
        await store.start()
        yield store
        await store.stop()

    async def test_state_storage_and_retrieval(self, store: InMemoryStateStore):
        """Test that state can be stored and retrieved."""
        state = "test_state_12345"
        data = {"ip": "192.168.1.1"}

        await store.set(f"oauth_state:{state}", data, ttl_seconds=300)
        retrieved = await store.get(f"oauth_state:{state}")

        assert retrieved == data

    async def test_state_one_time_use(self, store: InMemoryStateStore):
        """Test that state can only be used once (get_and_delete)."""
        state = "test_state_12345"
        data = {"ip": "192.168.1.1"}

        await store.set(f"oauth_state:{state}", data, ttl_seconds=300)

        # First retrieval should succeed
        first_retrieval = await store.get_and_delete(f"oauth_state:{state}")
        assert first_retrieval == data

        # Second retrieval should return None (state deleted)
        second_retrieval = await store.get_and_delete(f"oauth_state:{state}")
        assert second_retrieval is None

    async def test_state_expiry(self, store: InMemoryStateStore):
        """Test that expired state returns None."""
        import asyncio

        state = "test_state_12345"
        data = {"ip": "192.168.1.1"}

        # Store with very short TTL
        await store.set(f"oauth_state:{state}", data, ttl_seconds=1)

        # Wait for expiry
        await asyncio.sleep(1.5)

        # Should return None after expiry
        retrieved = await store.get(f"oauth_state:{state}")
        assert retrieved is None

    async def test_invalid_state_not_found(self, store: InMemoryStateStore):
        """Test that unknown state returns None."""
        result = await store.get("oauth_state:nonexistent_state")
        assert result is None

    async def test_state_deletion(self, store: InMemoryStateStore):
        """Test explicit state deletion."""
        state = "test_state_12345"
        data = {"ip": "192.168.1.1"}

        await store.set(f"oauth_state:{state}", data)

        # Delete should return True
        deleted = await store.delete(f"oauth_state:{state}")
        assert deleted is True

        # Second delete should return False
        deleted_again = await store.delete(f"oauth_state:{state}")
        assert deleted_again is False

    async def test_concurrent_state_access(self, store: InMemoryStateStore):
        """Test concurrent access to same state (race condition simulation)."""
        import asyncio

        state = "test_state_12345"
        data = {"ip": "192.168.1.1"}

        await store.set(f"oauth_state:{state}", data)

        # Simulate two concurrent get_and_delete calls
        results = await asyncio.gather(
            store.get_and_delete(f"oauth_state:{state}"),
            store.get_and_delete(f"oauth_state:{state}"),
        )

        # Only one should succeed, the other should get None
        successful = [r for r in results if r is not None]
        assert len(successful) == 1
        assert successful[0] == data
