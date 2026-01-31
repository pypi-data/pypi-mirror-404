"""Fixtures for extension tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest.fixture
def async_session() -> AsyncSession:
    """Create a mock async session for unit tests."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.begin_nested = MagicMock()
    return session


@pytest.fixture
def async_session_factory(async_session) -> async_sessionmaker:
    """Create a mock session factory for unit tests."""
    factory = MagicMock(spec=async_sessionmaker)
    factory.return_value = async_session
    return factory
