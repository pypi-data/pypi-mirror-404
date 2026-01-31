"""Configuration for IdentityPlanKit.

This module provides flexible configuration options:

1. Direct instantiation with explicit values (recommended for integration):
   ```python
   config = IdentityPlanKitConfig(
       database_url="postgresql+asyncpg://...",
       secret_key="...",
   )
   ```

2. From environment variables with custom prefix:
   ```python
   config = IdentityPlanKitConfig.from_env(prefix="MYAPP_AUTH_")
   ```

3. From any Pydantic settings object with field mapping:
   ```python
   config = IdentityPlanKitConfig.from_settings(
       my_settings,
       mapping={
           "database_url": "pg.url",
           "secret_key": "jwt.secret",
       }
   )
   ```

4. Default IPK_ prefix (backward compatible):
   ```python
   config = IdentityPlanKitConfig()  # Reads IPK_* env vars
   ```
"""

from __future__ import annotations

import os
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from collections.abc import Mapping

    from identity_plan_kit.shared.registry import ExtensionConfig


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


def _create_settings_class(env_prefix: str) -> type[BaseSettings]:
    """Dynamically create a settings class with custom env prefix."""

    class DynamicConfig(BaseSettings):
        model_config = SettingsConfigDict(
            env_prefix=env_prefix,
            env_file=(".env.local", ".env"),
            env_file_encoding="utf-8",
            extra="ignore",
        )

    return DynamicConfig


def _get_nested_attr(obj: Any, path: str) -> Any:
    """Get nested attribute using dot notation (e.g., 'pg.url')."""
    parts = path.split(".")
    value = obj
    for part in parts:
        if hasattr(value, part):
            value = getattr(value, part)
        elif isinstance(value, dict):
            value = value[part]
        else:
            raise AttributeError(f"Cannot resolve path '{path}' at '{part}'")
    return value


class IdentityPlanKitConfig(BaseSettings):
    """
    Configuration for IdentityPlanKit.

    Flexible configuration that supports multiple initialization patterns:

    1. **Direct instantiation** (recommended for integrations):
       ```python
       config = IdentityPlanKitConfig(
           database_url=settings.pg.url,
           secret_key=settings.jwt.secret,
           google_client_id=settings.oauth.google_client_id,
           # ... other required fields
       )
       ```

    2. **From environment with custom prefix**:
       ```python
       # Reads MYAPP_DATABASE_URL, MYAPP_SECRET_KEY, etc.
       config = IdentityPlanKitConfig.from_env(prefix="MYAPP_")
       ```

    3. **From existing Pydantic settings with mapping**:
       ```python
       config = IdentityPlanKitConfig.from_settings(
           my_settings,
           mapping={
               "database_url": "pg.url",  # dot notation for nested
               "secret_key": "jwt.secret",
               "google_client_id": "oauth.google.client_id",
           }
       )
       ```

    4. **Default (backward compatible)** - reads IPK_* environment variables:
       ```python
       config = IdentityPlanKitConfig()
       ```

    Required fields (must be provided via any method):
        - database_url: PostgreSQL async connection string
        - secret_key: JWT signing secret (min 32 chars)
        - google_client_id: Google OAuth client ID
        - google_client_secret: Google OAuth client secret
        - google_redirect_uri: OAuth callback URL
    """

    model_config = SettingsConfigDict(
        env_prefix="IPK_",
        # Support custom env file via IPK_ENV_FILE, then .env.local, then .env
        env_file=os.getenv("IPK_ENV_FILE") or (".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment (development, staging, production)",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | None = Field(
        default=None,
        description="Log level override. If not set, defaults to DEBUG in development "
        "and INFO in other environments.",
    )

    # Database
    database_url: str = Field(
        ...,
        description="PostgreSQL async connection string",
        examples=["postgresql+asyncpg://user:pass@localhost:5432/db"],
    )
    database_echo: bool = Field(
        default=False,
        description="Echo SQL queries (useful for debugging)",
    )
    database_pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Database connection pool size",
    )
    # P2 FIX: Statement timeout to prevent slow queries from holding connections
    database_statement_timeout_ms: int = Field(
        default=30000,
        ge=1000,
        le=300000,
        description="PostgreSQL statement timeout in milliseconds (30s default). "
        "Prevents slow queries from holding connections indefinitely.",
    )

    # Security
    secret_key: SecretStr = Field(
        ...,
        min_length=32,
        description="Secret key for JWT signing (min 32 chars)",
    )
    algorithm: Literal["HS256", "HS384", "HS512"] = Field(
        default="HS256",
        description="JWT signing algorithm",
    )

    # Tokens
    access_token_expire_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,
        description="Access token expiration in minutes",
    )
    refresh_token_expire_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Refresh token expiration in days",
    )

    # Google OAuth
    google_client_id: str = Field(
        ...,
        description="Google OAuth client ID",
    )
    google_client_secret: SecretStr = Field(
        ...,
        description="Google OAuth client secret",
    )
    google_redirect_uri: str = Field(
        ...,
        description="Google OAuth redirect URI",
        examples=["https://myapp.com/auth/google/callback"],
    )

    # Cookies
    cookie_domain: str | None = Field(
        default=None,
        description="Cookie domain (None for current domain)",
    )
    cookie_secure: bool = Field(
        default=True,
        description="Use secure cookies (HTTPS only)",
    )
    cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax",
        description="Cookie SameSite policy",
    )

    # Features
    enable_remember_me: bool = Field(
        default=True,
        description="Enable persistent sessions via refresh tokens",
    )
    enable_usage_tracking: bool = Field(
        default=True,
        description="Enable feature usage tracking",
    )

    # Caching
    permission_cache_ttl_seconds: int = Field(
        default=60,
        ge=0,
        le=3600,
        description="Permission cache TTL in seconds (0 to disable)",
    )
    plan_cache_ttl_seconds: int = Field(
        default=300,
        ge=0,
        le=3600,
        description="Plan cache TTL in seconds (0 to disable). "
        "Applies to both plan data and user plan assignments.",
    )

    # Redis (for distributed deployments)
    redis_url: str | None = Field(
        default=None,
        description="Redis URL for distributed state storage (OAuth CSRF tokens). "
        "Required for multi-instance deployments. "
        "Example: redis://localhost:6379/0",
    )
    require_redis: bool | None = Field(
        default=None,
        description="If True, fail startup if Redis is unavailable. "
        "Defaults to True in production when redis_url is set. "
        "Set explicitly to False to allow in-memory fallback in production.",
    )

    # API prefix
    api_prefix: str = Field(
        default="",
        description="Global API prefix for all routes (e.g., '/api/v1'). "
        "All routes will be mounted under this prefix.",
    )
    auth_prefix: str = Field(
        default="/auth",
        description="Auth routes prefix (appended to api_prefix)",
    )

    # Default role for new users (by code)
    default_role_code: str = Field(
        default="user",
        description="Default role code for new users (e.g., 'user', 'admin')",
    )

    # Default plan for new users (by code)
    default_plan_code: str = Field(
        default="free",
        description="Default plan code for new users (e.g., 'free', 'pro')",
    )

    # OAuth state TTL
    oauth_state_ttl_seconds: int = Field(
        default=300,
        ge=60,
        le=600,
        description="OAuth state token TTL in seconds (5 minutes default)",
    )

    # OAuth security - strict user-agent verification
    oauth_strict_ua_verification: bool = Field(
        default=False,
        description="If True, block OAuth callbacks with user-agent mismatch. "
        "Provides stronger CSRF protection but may cause false positives "
        "(browser updates, extensions). Recommended for high-security environments.",
    )

    # OAuth redirect URLs (for frontend redirect after authentication)
    oauth_allowed_redirect_urls: list[str] = Field(
        default_factory=list,
        description="List of allowed redirect URL prefixes for OAuth flow. "
        "After successful OAuth authentication, users can be redirected to URLs "
        "starting with these prefixes. Example: ['https://myapp.com', 'https://staging.myapp.com']. "
        "For security, exact prefix matching is used to prevent open redirect attacks.",
    )

    # Usage tracking lifetime period boundaries
    lifetime_period_start_year: int = Field(
        default=2000,
        description="Start year for lifetime usage period",
    )
    lifetime_period_end_year: int = Field(
        default=2100,
        description="End year for lifetime usage period",
    )

    # Graceful shutdown
    shutdown_grace_period_seconds: float = Field(
        default=5.0,
        ge=0.0,
        le=60.0,
        description="Grace period in seconds to allow in-flight requests to complete during shutdown",
    )

    # Token refresh idempotency
    token_refresh_idempotency_ttl_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        description="TTL for token refresh idempotency cache in seconds. "
        "Allows clients to safely retry refresh requests within this window.",
    )

    # Quota consumption idempotency
    quota_idempotency_ttl_seconds: int = Field(
        default=60,
        ge=0,
        le=300,
        description="TTL for quota consumption idempotency cache in seconds. "
        "When an idempotency_key is provided to check_and_consume_quota(), "
        "duplicate requests within this window return the cached result "
        "instead of consuming quota again. Set to 0 to disable idempotency.",
    )

    # Rate limiting
    rate_limit_login: str = Field(
        default="20/minute",
        description="Rate limit for login endpoint",
    )
    rate_limit_callback: str = Field(
        default="10/minute",
        description="Rate limit for OAuth callback endpoint",
    )
    rate_limit_refresh: str = Field(
        default="30/minute",
        description="Rate limit for token refresh endpoint",
    )
    rate_limit_logout: str = Field(
        default="10/minute",
        description="Rate limit for logout endpoint",
    )
    rate_limit_profile: str = Field(
        default="60/minute",
        description="Rate limit for profile endpoints (/auth/me, /auth/profile)",
    )
    rate_limit_plans: str = Field(
        default="60/minute",
        description="Rate limit for plan endpoints (/plans)",
    )

    # Proxy settings
    trust_proxy_headers: bool = Field(
        default=False,
        description="Trust X-Forwarded-For headers for client IP detection. "
        "Only enable this when running behind a trusted reverse proxy.",
    )

    # Metrics (optional - requires prometheus-client)
    enable_metrics: bool = Field(
        default=False,
        description="Enable Prometheus metrics endpoint. Requires 'metrics' extra: "
        "pip install identity-plan-kit[metrics]",
    )
    metrics_path: str = Field(
        default="/metrics",
        description="Path for Prometheus metrics endpoint",
    )

    # Admin panel authentication
    admin_email: str | None = Field(
        default=None,
        description="Superadmin email for SQLAdmin panel access. "
        "This user has full permissions (create, edit, delete). "
        "Required if using built-in admin authentication.",
    )
    admin_password: SecretStr | None = Field(
        default=None,
        min_length=8,
        description="Superadmin password for SQLAdmin panel access. "
        "Must be at least 8 characters. Required if admin_email is set.",
    )

    # Extension configuration for custom models/entities/DTOs
    # Not a Pydantic field - excluded from env var parsing
    _extension_config: "ExtensionConfig | None" = None

    @property
    def extension_config(self) -> "ExtensionConfig | None":
        """
        Get the extension configuration.

        Extension config allows customizing model/entity/DTO classes
        used by the library. This enables extending the built-in models
        with additional fields without modifying library code.

        Example:
            ```python
            from identity_plan_kit.shared.registry import (
                ExtensionConfig, ModelRegistry, EntityRegistry
            )

            extension_config = ExtensionConfig(
                models=ModelRegistry(user_model=ExtendedUserModel),
                entities=EntityRegistry(user_entity=ExtendedUser),
            )
            config = IdentityPlanKitConfig(
                # ... other config ...
            )
            config.set_extension_config(extension_config)
            ```
        """
        return self._extension_config

    def set_extension_config(self, extension_config: "ExtensionConfig | None") -> None:
        """
        Set the extension configuration.

        This must be called after creating the config if you want to use
        custom model/entity/DTO classes.

        Args:
            extension_config: Extension configuration with custom classes
        """
        object.__setattr__(self, "_extension_config", extension_config)

    @model_validator(mode="after")
    def _set_require_redis_default(self) -> "IdentityPlanKitConfig":
        """
        Auto-set require_redis based on environment and redis_url.

        In production with redis_url set, require_redis defaults to True.
        This prevents silent fallback to in-memory storage which breaks
        multi-instance deployments.
        """
        if self.require_redis is None:
            # Default: True in production with Redis URL, False otherwise
            if self.environment == Environment.PRODUCTION and self.redis_url:
                object.__setattr__(self, "require_redis", True)
            else:
                object.__setattr__(self, "require_redis", False)
        return self

    @model_validator(mode="after")
    def _validate_admin_credentials(self) -> "IdentityPlanKitConfig":
        """
        Validate that admin credentials are provided together.

        If admin_email is set, admin_password must also be set.
        """
        if self.admin_email is not None and self.admin_password is None:
            raise ValueError(
                "admin_password is required when admin_email is set. "
                "Both IPK_ADMIN_EMAIL and IPK_ADMIN_PASSWORD must be provided."
            )
        if self.admin_password is not None and self.admin_email is None:
            raise ValueError(
                "admin_email is required when admin_password is set. "
                "Both IPK_ADMIN_EMAIL and IPK_ADMIN_PASSWORD must be provided."
            )
        return self

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == Environment.PRODUCTION

    @classmethod
    def from_env(
        cls,
        prefix: str = "IPK_",
        env_file: str | tuple[str, ...] | None = (".env.local", ".env"),
    ) -> "IdentityPlanKitConfig":
        """
        Create configuration from environment variables with custom prefix.

        This allows integrating applications to use their own env var naming.

        Args:
            prefix: Environment variable prefix (default: "IPK_")
            env_file: Path(s) to .env file(s) to load

        Returns:
            IdentityPlanKitConfig instance

        Example:
            ```python
            # Reads MYAPP_DATABASE_URL, MYAPP_SECRET_KEY, etc.
            config = IdentityPlanKitConfig.from_env(prefix="MYAPP_")

            # Reads AUTH_DATABASE_URL, AUTH_SECRET_KEY, etc.
            config = IdentityPlanKitConfig.from_env(
                prefix="AUTH_",
                env_file=".env.production"
            )
            ```
        """
        # Get all field names from the model
        field_names = list(cls.model_fields.keys())

        # Build kwargs from environment with custom prefix
        kwargs: dict[str, Any] = {}
        for field_name in field_names:
            env_var = f"{prefix}{field_name.upper()}"
            value = os.environ.get(env_var)
            if value is not None:
                kwargs[field_name] = value

        # If env_file is provided and we have missing required fields,
        # try to load from the env file with the custom prefix
        if env_file:
            try:
                from dotenv import dotenv_values  # noqa: PLC0415

                env_files = (env_file,) if isinstance(env_file, str) else env_file
                for ef in env_files:
                    if os.path.exists(ef):
                        env_values = dotenv_values(ef)
                        for field_name in field_names:
                            if field_name not in kwargs:
                                env_var = f"{prefix}{field_name.upper()}"
                                if env_var in env_values:
                                    kwargs[field_name] = env_values[env_var]
            except ImportError:
                pass  # dotenv not installed, skip file loading

        return cls(**kwargs)

    @classmethod
    def from_settings(
        cls,
        settings: Any,
        mapping: Mapping[str, str] | None = None,
    ) -> "IdentityPlanKitConfig":
        """
        Create configuration from any Pydantic settings object.

        This is the most flexible option for integrating with existing
        applications that have their own configuration structure.

        Args:
            settings: Any object with attributes (Pydantic model, dataclass, etc.)
            mapping: Optional dict mapping IPK field names to settings paths.
                     Uses dot notation for nested access (e.g., "pg.url").
                     If not provided, attempts to read fields with same names.

        Returns:
            IdentityPlanKitConfig instance

        Example:
            ```python
            # kinonee's settings structure:
            # settings.pg.url = "postgresql+asyncpg://..."
            # settings.jwt.secret = "..."
            # settings.google_oauth.client_id = "..."

            config = IdentityPlanKitConfig.from_settings(
                settings,
                mapping={
                    "database_url": "pg.url",
                    "secret_key": "jwt.secret",
                    "google_client_id": "google_oauth.client_id",
                    "google_client_secret": "google_oauth.client_secret",
                    "google_redirect_uri": "google_oauth.redirect_uri",
                    "redis_url": "redis.url",
                    "environment": "app.environment",
                }
            )
            ```
        """
        mapping = mapping or {}
        kwargs: dict[str, Any] = {}

        for field_name, field_info in cls.model_fields.items():
            value = None

            # First try the mapping
            if field_name in mapping:
                path = mapping[field_name]
                try:
                    value = _get_nested_attr(settings, path)
                except (AttributeError, KeyError):
                    pass  # Path not found, will use default or fail on required

            # If no mapping or mapping failed, try direct attribute access
            if value is None and field_name not in mapping:
                try:
                    value = getattr(settings, field_name, None)
                except Exception:
                    pass

            # Handle SecretStr - extract value if it's already a SecretStr
            if value is not None:
                if hasattr(value, "get_secret_value"):
                    value = value.get_secret_value()
                kwargs[field_name] = value

        return cls(**kwargs)

    @classmethod
    def from_mapping(cls, **kwargs: Any) -> "IdentityPlanKitConfig":
        """
        Create configuration from explicit keyword arguments.

        This is a convenience method that's equivalent to direct instantiation
        but makes the intent clearer when reading code.

        Args:
            **kwargs: Configuration values

        Returns:
            IdentityPlanKitConfig instance

        Example:
            ```python
            config = IdentityPlanKitConfig.from_mapping(
                database_url=os.getenv("DATABASE_URL"),
                secret_key=os.getenv("JWT_SECRET"),
                google_client_id=os.getenv("GOOGLE_CLIENT_ID"),
                google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
                google_redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
            )
            ```
        """
        return cls(**kwargs)
