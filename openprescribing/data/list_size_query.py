from dataclasses import dataclass


@dataclass
class ListSizeQuery:
    """Represents a query returning list size data."""

    def to_params(self, field):
        """Serialize to URL query parameters.

        This is intentionally blank!
        """

        return {}
