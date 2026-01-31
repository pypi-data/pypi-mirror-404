"""Shared constants for the identity-plan-kit library.

This module centralizes magic numbers and configuration defaults
to improve maintainability and make the codebase more configurable.
"""

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Default cache TTL in seconds (5 minutes)
DEFAULT_CACHE_TTL_SECONDS = 300

# Maximum entries in in-memory caches before cleanup
DEFAULT_MAX_CACHE_ENTRIES = 10000

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================

# Socket timeouts for Redis connections (in seconds)
REDIS_SOCKET_TIMEOUT = 5.0
REDIS_SOCKET_CONNECT_TIMEOUT = 5.0

# Retry configuration for Redis operations
REDIS_RETRY_ATTEMPTS = 3
REDIS_RETRY_BASE_DELAY = 0.5  # seconds

# Circuit breaker configuration for Redis
REDIS_CIRCUIT_FAILURE_THRESHOLD = 5
REDIS_CIRCUIT_RECOVERY_TIMEOUT = 30.0  # seconds
REDIS_CIRCUIT_HALF_OPEN_MAX_CALLS = 2

# =============================================================================
# STATE STORE CONFIGURATION
# =============================================================================

# Maximum key length for state store keys
STATE_STORE_MAX_KEY_LENGTH = 256

# Maximum consecutive cleanup errors before critical warning
STATE_STORE_MAX_CONSECUTIVE_ERRORS = 5

# =============================================================================
# USER PROFILE CONSTRAINTS
# =============================================================================

# Display name constraints
USER_DISPLAY_NAME_MAX_LENGTH = 100
USER_DISPLAY_NAME_MIN_LENGTH = 1

# Picture URL constraints
USER_PICTURE_URL_MAX_LENGTH = 500

# =============================================================================
# OAUTH CONFIGURATION
# =============================================================================

# Maximum concurrent OAuth calls (bulkhead pattern)
OAUTH_MAX_CONCURRENT_CALLS = 10

# Timeout for semaphore acquisition (prevents indefinite waiting)
OAUTH_SEMAPHORE_ACQUIRE_TIMEOUT = 30.0  # seconds

# OAuth state token TTL
OAUTH_STATE_TTL_SECONDS = 300  # 5 minutes

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Default database pool size
DEFAULT_DATABASE_POOL_SIZE = 5

# Default max overflow for connection pool
DEFAULT_DATABASE_MAX_OVERFLOW = 10

# Default statement timeout in milliseconds
DEFAULT_DATABASE_STATEMENT_TIMEOUT_MS = 30000

# Connection pool recycle time (1 hour)
DATABASE_POOL_RECYCLE_SECONDS = 3600

# =============================================================================
# RETRY CONFIGURATION
# =============================================================================

# Default retry attempts for transient failures
DEFAULT_RETRY_ATTEMPTS = 3

# Default retry wait times
DEFAULT_RETRY_MIN_WAIT = 0.1  # seconds
DEFAULT_RETRY_MAX_WAIT = 2.0  # seconds

# Database startup retry configuration
DEFAULT_STARTUP_TIMEOUT = 30.0  # seconds
DEFAULT_CONNECTION_RETRY_ATTEMPTS = 5
DEFAULT_CONNECTION_RETRY_MAX_WAIT = 10.0  # seconds

# =============================================================================
# LOCKOUT CONFIGURATION
# =============================================================================

# Default maximum failed attempts before lockout
DEFAULT_LOCKOUT_MAX_ATTEMPTS = 5

# Default lockout duration in minutes
DEFAULT_LOCKOUT_DURATION_MINUTES = 15

# Default attempt tracking window in minutes
DEFAULT_LOCKOUT_WINDOW_MINUTES = 15

# =============================================================================
# TOKEN CONFIGURATION
# =============================================================================

# Default access token expiration in minutes
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 15

# Default refresh token expiration in days
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7

# Token refresh idempotency TTL in seconds
DEFAULT_TOKEN_REFRESH_IDEMPOTENCY_TTL_SECONDS = 10

# Quota idempotency TTL in seconds
DEFAULT_QUOTA_IDEMPOTENCY_TTL_SECONDS = 60

# =============================================================================
# ERROR FORMATTING
# =============================================================================

# Maximum error message length for database constraint violations
MAX_CONSTRAINT_ERROR_MESSAGE_LENGTH = 2000

# Maximum key length to display in error messages
MAX_KEY_DISPLAY_LENGTH = 50
