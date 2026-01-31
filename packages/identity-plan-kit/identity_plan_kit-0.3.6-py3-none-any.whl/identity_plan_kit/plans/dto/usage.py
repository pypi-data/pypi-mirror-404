"""Usage-related DTOs."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UsageInfo:
    """
    Feature usage information DTO.

    Represents the current usage state for a feature within a user's plan.
    This is an immutable value object for transferring usage data.
    """

    feature_code: str
    """The feature code this usage applies to."""

    used: int
    """Current usage count in the period."""

    limit: int
    """
    Usage limit for the period.
    -1 indicates unlimited usage.
    """

    period: str | None
    """
    Period type: 'daily', 'monthly', or None for lifetime.
    """

    remaining: int
    """
    Remaining usage in the period.
    -1 indicates unlimited remaining.
    """

    @property
    def is_unlimited(self) -> bool:
        """Check if this feature has unlimited usage."""
        return self.limit == -1

    @property
    def is_exhausted(self) -> bool:
        """Check if usage quota is exhausted."""
        if self.is_unlimited:
            return False
        return self.remaining <= 0

    @property
    def usage_percentage(self) -> float:
        """
        Get usage as percentage of limit.

        Returns:
            Percentage (0-100+), or 0.0 for unlimited features.
        """
        if self.is_unlimited or self.limit == 0:
            return 0.0
        return (self.used / self.limit) * 100
