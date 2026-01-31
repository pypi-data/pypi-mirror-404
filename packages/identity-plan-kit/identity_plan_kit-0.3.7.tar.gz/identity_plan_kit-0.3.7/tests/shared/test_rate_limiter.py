from identity_plan_kit.shared import rate_limiter


def test_rate_limiter_initialization_deadlock():
    """
    Test that get_rate_limiter() does not deadlock when create_limiter() is called.
    This was previously failing because of non-reentrant Lock.
    """
    # Reset global state for testing
    rate_limiter._limiter = None

    # This call should not hang
    limiter = rate_limiter.get_rate_limiter()
    assert limiter is not None

    # Second call should also work and return the same instance
    limiter2 = rate_limiter.get_rate_limiter()
    assert limiter2 is limiter


def test_manual_nested_lock():
    """
    Explicitly test that the lock is now re-entrant.
    """
    with rate_limiter._limiter_lock, rate_limiter._limiter_lock:
        # Should not hang
        pass
