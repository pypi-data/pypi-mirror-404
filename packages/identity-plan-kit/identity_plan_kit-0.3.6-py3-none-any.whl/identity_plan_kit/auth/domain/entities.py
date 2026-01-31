"""Auth domain entities."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


@dataclass
class User:
    """
    User domain entity.

    Represents an authenticated user in the system.

    Attributes:
        id: Unique user identifier (UUID7)
        email: User's email address
        role_id: Foreign key to the user's role (UUID)
        display_name: User's display name (from OAuth or user-edited)
        picture_url: Profile picture URL (from OAuth provider, nullable)
        is_active: Whether the user account is active
        is_verified: Whether the user's email is verified
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        role_code: Role code (e.g., "admin", "user") - populated when role is loaded
        permissions: User's permissions - NOT auto-populated by repository.
                    Use RBACService.get_user_permissions() to fetch and populate.
    """

    id: UUID
    email: str
    role_id: UUID
    display_name: str
    picture_url: str | None = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Loaded relations (optional - must be explicitly populated)
    role_code: str | None = None
    # P2 FIX: Added documentation clarifying this field is NOT auto-populated.
    # It exists for consumers who want to attach permissions after loading.
    # Use RBACService.get_user_permissions(user.id, user.role_id) to fetch.
    permissions: set[str] = field(default_factory=set)

    def deactivate(self) -> None:
        """
        Deactivate the user account.

        Note: updated_at is managed by the persistence layer (ORM).
        """
        if not self.is_active:
            raise ValueError("User is already inactive")
        self.is_active = False

    def activate(self) -> None:
        """
        Activate the user account.

        Note: updated_at is managed by the persistence layer (ORM).
        """
        if self.is_active:
            raise ValueError("User is already active")
        self.is_active = True

    def verify(self) -> None:
        """
        Mark user as verified.

        Note: updated_at is managed by the persistence layer (ORM).
        """
        if self.is_verified:
            raise ValueError("User is already verified")
        self.is_verified = True


@dataclass
class UserProvider:
    """
    OAuth provider link for a user.

    Links a user to an external OAuth provider (e.g., Google).
    """

    id: UUID
    user_id: UUID
    code: str  # e.g., "google"
    external_user_id: str  # Provider's user ID

    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        valid_codes = {"google"}  # Extend as needed
        if self.code not in valid_codes:
            raise ValueError(f"Invalid provider code: {self.code}")


@dataclass
class RefreshToken:
    """
    Refresh token for persistent sessions.

    Tokens are stored hashed in the database for security.
    """

    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    revoked_at: datetime | None = None
    user_agent: str | None = None
    ip_address: str | None = None

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(UTC) > self.expires_at

    @property
    def is_revoked(self) -> bool:
        """Check if token has been revoked."""
        return self.revoked_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)."""
        return not self.is_expired and not self.is_revoked

    def revoke(self) -> None:
        """Revoke this token."""
        if self.is_revoked:
            raise ValueError("Token is already revoked")
        self.revoked_at = datetime.now(UTC)
